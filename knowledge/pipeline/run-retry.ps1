$ErrorActionPreference = 'Continue'
$auditDir = 'C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07'
Set-Location $auditDir
$date = Get-Date -Format 'yyyy-MM-dd'
$logFile = "$auditDir\daily\retry-$date.log"
function Log($m) {
    $ts = Get-Date -Format 'HH:mm:ss'
    "[$ts] $m" | Tee-Object -FilePath $logFile -Append
}
Log "=== Retry Pipeline Starting ==="
try {
    node scripts\retry-failed-articles.cjs 2>&1 | Tee-Object -FilePath $logFile -Append
    Log "=== Retry completed ==="
} catch {
    Log "ERROR: $_"
}