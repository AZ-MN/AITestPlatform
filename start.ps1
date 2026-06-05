$ErrorActionPreference = 'Stop'

function Test-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw $InstallHint
    }
}

function Get-FreePort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$PreferredPort,
        [int]$SearchWindow = 20
    )

    for ($port = $PreferredPort; $port -le ($PreferredPort + $SearchWindow); $port++) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $listener) {
            return $port
        }
    }

    throw "No free port found near $PreferredPort."
}

function Wait-ForPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($listener) {
            return
        }

        Start-Sleep -Seconds 1
    }

    throw "Port $Port did not start listening within $TimeoutSeconds seconds."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $ErrorMessage
    }
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir 'backend'
$frontendDir = Join-Path $rootDir 'frontend'
$venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'
$runtimeDir = Join-Path $rootDir '.run'
$stateFile = Join-Path $runtimeDir 'aitestplatform-windows.json'
$backendProcess = $null
$frontendProcess = $null

function Save-State {
    param(
        [Parameter(Mandatory = $true)]
        [int]$BackendPid,
        [Parameter(Mandatory = $true)]
        [int]$BackendPort,
        [Parameter(Mandatory = $true)]
        [int]$FrontendPid,
        [Parameter(Mandatory = $true)]
        [int]$FrontendPort
    )

    if (-not (Test-Path $runtimeDir)) {
        New-Item -ItemType Directory -Path $runtimeDir | Out-Null
    }

    @{
        backendPid = $BackendPid
        backendPort = $BackendPort
        frontendPid = $FrontendPid
        frontendPort = $FrontendPort
        rootDir = $rootDir
        createdAt = (Get-Date).ToString('o')
    } | ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8
}

function Remove-State {
    if (Test-Path $stateFile) {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
    }
}

try {
    Set-Location $rootDir
    Remove-State

    Write-Host '========================================'
    Write-Host '  AI Test Case Platform - Startup Script'
    Write-Host '========================================'

    Write-Host ''
    Write-Host '[1/4] Checking runtime prerequisites...'
    Test-Command -Name 'python' -InstallHint 'Python 3.9+ is required.'
    Test-Command -Name 'node' -InstallHint 'Node.js 18+ is required.'
    Test-Command -Name 'npm' -InstallHint 'npm is required. Please reinstall Node.js if needed.'

    $backendPort = Get-FreePort -PreferredPort 8000
    $frontendPort = Get-FreePort -PreferredPort 5173

    if ($backendPort -ne 8000) {
        Write-Host "[WARN] Port 8000 is busy. Backend will use $backendPort"
    }
    if ($frontendPort -ne 5173) {
        Write-Host "[WARN] Port 5173 is busy. Frontend will use $frontendPort"
    }

    Write-Host ''
    Write-Host '[2/4] Installing backend dependencies and starting service...'
    if (-not (Test-Path $venvPython)) {
        Invoke-Checked -Command { python -m venv "$backendDir\.venv" } -ErrorMessage 'Failed to create backend virtual environment.'
        Write-Host 'Backend virtual environment created.'
    }

    Invoke-Checked -Command { & $venvPython -m pip install -r (Join-Path $backendDir 'requirements.txt') -q } -ErrorMessage 'Failed to install backend dependencies.'

    $envFile = Join-Path $backendDir '.env'
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $backendDir '.env.example') $envFile
        Write-Host '[WARN] Created backend/.env. Add AI model API keys if needed.'
    }

    $backendProcess = Start-Process -FilePath $venvPython -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', $backendPort, '--reload') -WorkingDirectory $backendDir -PassThru
    Wait-ForPort -Port $backendPort -TimeoutSeconds 15

    Write-Host ''
    Write-Host '[3/4] Installing frontend dependencies and starting service...'
    if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
        Invoke-Checked -Command { npm install --cache (Join-Path $env:TEMP 'npm-cache') --no-audit --no-fund } -ErrorMessage 'Failed to install frontend dependencies.'
    }

    $env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$backendPort"
    try {
        $frontendProcess = Start-Process -FilePath 'npm.cmd' -ArgumentList @('run', 'dev', '--', '--host', '0.0.0.0', '--port', $frontendPort) -WorkingDirectory $frontendDir -PassThru
    }
    finally {
        Remove-Item Env:VITE_API_PROXY_TARGET -ErrorAction SilentlyContinue
    }

    Wait-ForPort -Port $frontendPort -TimeoutSeconds 30
    Save-State -BackendPid $backendProcess.Id -BackendPort $backendPort -FrontendPid $frontendProcess.Id -FrontendPort $frontendPort

    Write-Host ''
    Write-Host '[4/4] Startup summary'
    Write-Host '========================================'
    Write-Host '  Startup completed.'
    Write-Host ''
    Write-Host "  Frontend: http://127.0.0.1:$frontendPort"
    Write-Host "  Backend API: http://127.0.0.1:$backendPort/api/v1"
    Write-Host "  API docs: http://127.0.0.1:$backendPort/docs"
    Write-Host "  Frontend proxy: http://127.0.0.1:$backendPort"
    Write-Host "  Stop command: .\\stop.bat"
    Write-Host ''
    Write-Host '  Default account: admin / Admin@123'
    Write-Host '========================================'

    exit 0
}
catch {
    Remove-State
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }

    Write-Host ''
    Write-Host "[ERROR] $($_.Exception.Message)"
    exit 1
}