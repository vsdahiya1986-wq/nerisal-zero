"""
Corridor & Route Agent (Route / Logistics)
Keeps a live road graph, computes travel times for every unit to every incident and
from every incident to every hospital. Inside the venue, vehicle speed drops with
crowd density (this is exactly why ambulances could not reach victims at Karur),
unless the Gate 4 emergency corridor has been opened and cleared.
"""
import networkx as nx

from .geo import haversine_km

ROAD_KMH = 25.0      # urban ambulance average incl. junctions
VENUE_KMH = 6.0      # vehicle inching through a crowd, before density penalty
CORRIDOR_KMH = 15.0  # cleared corridor
WALK_KMH = 3.0       # on-foot teams inside the venue


class RouteAgent:
    name = "Corridor & Route Agent"

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def crowd_factor(self, st):
        d = max(st["zones"]["A"]["density"], st["zones"]["B"]["density"])
        return 1.0 + max(0.0, d - 2.0) * 1.0

    def build_graph(self, st):
        g = nx.Graph()
        cf = self.crowd_factor(st)
        corridor = st["gates"]["G4"]["open"]
        for a, b, name, kind in self.edges:
            if frozenset((a, b)) in st["blocked"]:
                continue
            km = haversine_km(self.nodes[a], self.nodes[b])
            if kind == "road":
                mins = km * 1.3 / ROAD_KMH * 60
            elif kind == "venue":
                mins = max(0.2, km) / VENUE_KMH * 60 * cf
            else:  # emergency corridor through Gate 4
                if not corridor:
                    continue
                mins = max(0.2, km) / CORRIDOR_KMH * 60
            g.add_edge(a, b, minutes=round(mins, 2), name=name)
        return g

    def run(self, st, log):
        g = self.build_graph(st)
        self.g = g
        self.dist = {}
        self._cf = self.crowd_factor(st)
        st["route_info"] = {"crowd_factor": round(self._cf, 2), "corridor_open": st["gates"]["G4"]["open"]}
        return g

    def node_of_incident(self, inc):
        return "J_HOPE" if inc["location"] == "J_HOPE" else "VENUE"

    def sp(self, a, b):
        key = (a, b)
        if key not in self.dist:
            try:
                self.dist[key] = nx.shortest_path_length(self.g, a, b, weight="minutes")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                self.dist[key] = None
        return self.dist[key]

    def path(self, a, b):
        try:
            return nx.shortest_path(self.g, a, b, weight="minutes")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def eta(self, st, unit, inc):
        """Minutes for unit to reach incident, or None if it cannot."""
        in_venue = inc["location"] in st["zones"]
        if unit["mode"] == "foot":
            if not in_venue or unit.get("node", "").startswith("J_") or unit.get("node", "").startswith("B_"):
                return None
            z = st["zones"][inc["location"]]
            km = haversine_km((unit["lat"], unit["lng"]), (z["lat"], z["lng"]))
            dens = z["density"]
            return round(1.0 + km / WALK_KMH * 60 * (1 + max(0, dens - 3) * 0.4), 1)
        start = unit["node"]
        if start not in self.nodes:
            return None
        t = self.sp(start, self.node_of_incident(inc))
        if t is None:
            return None
        return round(t + 0.5, 1)

    def eta_to_hospital(self, inc, hid):
        t = self.sp(self.node_of_incident(inc), hid)
        return None if t is None else round(t, 1)
