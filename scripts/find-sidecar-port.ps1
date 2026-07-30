# find-sidecar-port.ps1
# Discovers the port the Enterprise AI Companion Python sidecar is listening on.
# Run this while the Tauri app is open to get the port for curl/Postman testing.
#
# Usage:
#   .\scripts\find-sidecar-port.ps1
#
# Output:
#   Sidecar port: 51234
#   Base URL:     http://localhost:51234

$pythonProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue

if (-not $pythonProcs) {
    Write-Host "No Python processes found. Is the Tauri app running?" -ForegroundColor Red
    exit 1
}

$port = $null

foreach ($proc in $pythonProcs) {
    $pid = $proc.Id
    $connections = netstat -ano 2>$null | Select-String "LISTENING" | Select-String "\s$pid$"
    foreach ($line in $connections) {
        if ($line -match ":(\d{4,5})\s") {
            $candidatePort = [int]$Matches[1]
            # Skip well-known ports (system services, not our sidecar)
            if ($candidatePort -gt 1024 -and $candidatePort -lt 65000) {
                # Verify it responds to our health endpoint
                try {
                    $response = Invoke-RestMethod -Uri "http://localhost:$candidatePort/health" `
                        -Method GET -TimeoutSec 2 -ErrorAction Stop
                    if ($response.status -eq "ok") {
                        $port = $candidatePort
                        break
                    }
                } catch {
                    # Not our sidecar — keep looking
                }
            }
        }
    }
    if ($port) { break }
}

if ($port) {
    Write-Host ""
    Write-Host "Sidecar port: $port" -ForegroundColor Green
    Write-Host "Base URL:     http://localhost:$port" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Example commands:" -ForegroundColor Yellow
    Write-Host "  curl http://localhost:$port/health"
    Write-Host "  curl -X POST http://localhost:$port/indexing/start -H 'Content-Type: application/json' -d '{\"workspace_path\": \"C:/TestDocs\"}'"
    Write-Host "  curl -X POST http://localhost:$port/search/hybrid -H 'Content-Type: application/json' -d '{\"query\": \"your question\", \"top_k\": 5}'"
    Write-Host ""
    # Copy to clipboard if available
    $port | Set-Clipboard -ErrorAction SilentlyContinue
    Write-Host "(Port copied to clipboard)" -ForegroundColor DarkGray
} else {
    Write-Host "Could not find the sidecar. Make sure the Tauri app is fully started (wait for the orb to appear)." -ForegroundColor Red
}
