# NERISAL ZERO - overnight runner
# Restarts Claude Code every 10 minutes until the plan says ALL DONE or it is 07:15.
# If Claude hits a usage limit, the run simply ends; this loop waits and tries again after the limit resets.
# Run from the project folder:   powershell -ExecutionPolicy Bypass -File .\night_runner.ps1

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

# Deadline: next 07:15 local time
$now = Get-Date
$deadline = (Get-Date -Hour 7 -Minute 15 -Second 0)
if ($now -gt $deadline) { $deadline = $deadline.AddDays(1) }
Write-Host "Night runner started $now. Will stop at $deadline." -ForegroundColor Cyan

$instruction = "Read NIGHT_PROMPT.md in this folder and follow it exactly. Start with section 0. Work autonomously; do not ask questions."
$run = 0

while ((Get-Date) -lt $deadline) {
    if ((Test-Path .\NIGHT_PLAN.md) -and (Select-String -Path .\NIGHT_PLAN.md -Pattern "ALL DONE" -Quiet)) {
        Write-Host "Plan says ALL DONE. Stopping." -ForegroundColor Green
        break
    }
    $run++
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "`n===== RUN $run at $stamp =====" | Tee-Object -FilePath .\night_runner.log -Append

    claude -p $instruction --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath .\night_runner.log -Append

    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "===== RUN $run ended at $stamp (exit $LASTEXITCODE). Waiting 10 minutes. =====" | Tee-Object -FilePath .\night_runner.log -Append
    Start-Sleep -Seconds 600
}

# Safety net: if the deadline passed before the wrap-up, ask for the wrap-up once.
if (-not ((Test-Path .\NIGHT_PLAN.md) -and (Select-String -Path .\NIGHT_PLAN.md -Pattern "ALL DONE" -Quiet))) {
    claude -p "Read NIGHT_PROMPT.md. It is past 07:15: do ONLY section 6 (Final wrap-up) now." --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath .\night_runner.log -Append
}
Write-Host "Night runner finished at $(Get-Date). Read MORNING_REPORT.md." -ForegroundColor Green
