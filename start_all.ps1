$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

Get-Process ssh -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-Item tunnel.out.log -ErrorAction SilentlyContinue

Start-Process cmd.exe -ArgumentList "/c", "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:8080 serveo.net > tunnel.out.log 2>&1" -WindowStyle Hidden
Write-Host "Wait for tunnel..."
Start-Sleep -Seconds 13

$line = Get-Content tunnel.out.log -ErrorAction SilentlyContinue | Select-String "Forwarding HTTP" | Select-Object -First 1
$url = [regex]::Match($line, "https://\S+").Value.Trim()
if (-not $url) {
    Write-Host "Cannot get tunnel URL. See tunnel.out.log"
    exit 1
}
Write-Host "Tunnel URL: $url"

(Get-Content .env) -replace '^WEBAPP_URL=.*', "WEBAPP_URL=$url" | Set-Content .env
Write-Host "WEBAPP_URL updated in .env"

Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "shop_bot\\bot.py" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

$cmdline = 'cmd.exe /c ""' + $dir + '\.venv\Scripts\python.exe" "' + $dir + '\bot.py" > "' + $dir + '\bot.out.log" 2> "' + $dir + '\bot.err.log""'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CurrentDirectory = $dir; CommandLine = $cmdline }
Start-Sleep -Seconds 8

Write-Host "Bot PID: $($r.ProcessId)"
Get-Content bot.err.log -Tail 3
Write-Host ""
Write-Host "Mini App URL: $url"
Write-Host "Don't forget: add this domain in BotFather -> /setdomain"