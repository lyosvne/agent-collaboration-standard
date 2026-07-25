$ErrorActionPreference = 'Continue'
$auditDir = 'C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07'
Set-Location $auditDir
$date = Get-Date -Format 'yyyy-MM-dd'
$logFile = "$auditDir\daily\scheduler-$date.log"
function Log($m) {
    $ts = Get-Date -Format 'HH:mm:ss'
    "[$ts] $m" | Tee-Object -FilePath $logFile -Append
}
Log "=== Daily Pipeline Starting ==="
try {
    node daily\daily-pipeline.cjs 2>&1 | Tee-Object -FilePath $logFile -Append
    Log "=== Pipeline completed ==="
} catch {
    Log "ERROR: $_"
}