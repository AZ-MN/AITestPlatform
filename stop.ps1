$ErrorActionPreference = 'Stop'

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $rootDir '.run'
$stateFile = Join-Path $runtimeDir 'aitestplatform-windows.json'

function Remove-State {
    if (Test-Path $stateFile) {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($process) {
        taskkill /PID $ProcessId /T /F | Out-Null
        return $true
    }

    return $false
}

function Stop-ProjectProcessesByCommandLine {
    $patterns = @(
        '*AITestPlatform\\backend\\.venv\\Scripts\\python.exe *app.main:app*',
        '*AITestPlatform\\frontend*vite*',
        '*AITestPlatform\\frontend*npm run dev*'
    )

    $processes = Get-CimInstance Win32_Process | Where-Object {
        $commandLine = $_.CommandLine
        if (-not $commandLine) {
            return $false
        }

        foreach ($pattern in $patterns) {
            if ($commandLine -like $pattern) {
                return $true
            }
        }

        return $false
    }

    $stopped = $false
    foreach ($process in $processes) {
        taskkill /PID $process.ProcessId /T /F | Out-Null
        $stopped = $true
    }

    return $stopped
}

try {
    Write-Host '========================================'
    Write-Host '  AI Test Case Platform - Stop Script'
    Write-Host '========================================'

    $stopped = $false
    if (Test-Path $stateFile) {
        $state = Get-Content $stateFile -Raw | ConvertFrom-Json

        if ($state.frontendPid) {
            $stopped = (Stop-ProcessTree -ProcessId ([int]$state.frontendPid)) -or $stopped
        }
        if ($state.backendPid) {
            $stopped = (Stop-ProcessTree -ProcessId ([int]$state.backendPid)) -or $stopped
        }
    }

    $stopped = (Stop-ProjectProcessesByCommandLine) -or $stopped
    Remove-State

    if ($stopped) {
        Write-Host ''
        Write-Host 'Services stopped.'
    }
    else {
        Write-Host ''
        Write-Host 'No running AITestPlatform services found.'
    }

    exit 0
}
catch {
    Write-Host ''
    Write-Host "[ERROR] $($_.Exception.Message)"
    exit 1
}