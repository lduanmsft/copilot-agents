<#
.SYNOPSIS
    Check and install prerequisites for MaoQiuQiu (毛球球)
.DESCRIPTION
    Verifies Node.js, Azure CLI, enghub-mcp, azmcp are installed.
    Offers to install missing dependencies.
.EXAMPLE
    .\Setup-Prerequisites.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MaoQiuQiu Prerequisites Check" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# --- 1. Node.js ---
Write-Host "[1/6] Node.js ... " -NoNewline
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVer = (node --version 2>&1).ToString().Trim()
    Write-Host "OK ($nodeVer)" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND" -ForegroundColor Red
    $install = Read-Host "       Install Node.js LTS now? (y/n)"
    if ($install -eq 'y') {
        Write-Host "       Installing Node.js via winget..." -ForegroundColor Cyan
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements 2>&1
        Write-Host "       Done. Please restart this script after installation." -ForegroundColor Yellow
    } else {
        Write-Host "       Manual: winget install OpenJS.NodeJS.LTS" -ForegroundColor Yellow
    }
    $allGood = $false
Write-Host "[2/6] npx ... " -NoNewline
$npx = Get-Command npx -ErrorAction SilentlyContinue
if ($npx) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND (comes with Node.js)" -ForegroundColor Red
    $allGood = $false
}

# --- 3. Azure CLI ---
Write-Host "[3/6] Azure CLI (az) ... " -NoNewline
$az = Get-Command az -ErrorAction SilentlyContinue
if ($az) {
    $azVer = (az version --output tsv 2>&1 | Select-Object -First 1).ToString().Trim()
    Write-Host "OK ($azVer)" -ForegroundColor Green
    
    # Check az login status
    Write-Host "       Checking az login ... " -NoNewline
    $account = az account show --output json 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($account.user) {
        Write-Host "logged in as $($account.user.name)" -ForegroundColor Green
    } else {
        Write-Host "NOT LOGGED IN" -ForegroundColor Yellow
        Write-Host "       Run: az login" -ForegroundColor Yellow
    }
} else {
    Write-Host "NOT FOUND" -ForegroundColor Red
    $install = Read-Host "       Install Azure CLI now? (y/n)"
    if ($install -eq 'y') {
        Write-Host "       Installing Azure CLI via winget..." -ForegroundColor Cyan
        winget install Microsoft.AzureCLI --accept-source-agreements --accept-package-agreements 2>&1
        Write-Host "       Done. Please restart this script, then run: az login" -ForegroundColor Yellow
    } else {
        Write-Host "       Manual: winget install Microsoft.AzureCLI" -ForegroundColor Yellow
    }
    $allGood = $false
}

# --- 4. azmcp (Azure MCP) ---
Write-Host "[4/6] azmcp (Azure MCP) ... " -NoNewline
$azmcp = Get-Command azmcp -ErrorAction SilentlyContinue
if ($azmcp) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND" -ForegroundColor Yellow
    Write-Host "       Install: az extension add --name mcp --allow-preview true" -ForegroundColor Yellow
    Write-Host "       Then:    pip install azure-mcp" -ForegroundColor Yellow
    $install = Read-Host "       Install now? (y/n)"
    if ($install -eq 'y') {
        az extension add --name mcp --allow-preview true 2>&1
        Write-Host "       Installed az mcp extension" -ForegroundColor Green
    }
}

# --- 5. enghub-mcp ---
Write-Host "[5/6] enghub-mcp ... " -NoNewline
$enghub = Get-Command enghub-mcp -ErrorAction SilentlyContinue
if ($enghub) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND" -ForegroundColor Yellow
    Write-Host "       Install options:" -ForegroundColor Yellow
    Write-Host "         Option A (recommended): gh release download" -ForegroundColor Yellow
    Write-Host "         Option B: npm install from source" -ForegroundColor Yellow
    Write-Host "       See: docs/setup-enghub-mcp.md for detailed instructions" -ForegroundColor Yellow
    $installEng = Read-Host "       Try auto-install via gh? Requires gh auth login to azure-core org (y/n)"
    if ($installEng -eq 'y') {
        $gh = Get-Command gh -ErrorAction SilentlyContinue
        if ($gh) {
            Write-Host "       Downloading enghub-mcp..." -ForegroundColor Cyan
            gh release download --repo azure-core/enghub-mcp-server-tools --pattern "azure-core-enghub-mcp.tgz" --output enghub-mcp.tgz --clobber 2>&1
            if (Test-Path "enghub-mcp.tgz") {
                npm install -g enghub-mcp.tgz 2>&1
                Remove-Item "enghub-mcp.tgz" -Force
                Write-Host "       enghub-mcp installed!" -ForegroundColor Green
            } else {
                Write-Host "       Download failed. Check gh auth and azure-core org access." -ForegroundColor Red
            }
        } else {
            Write-Host "       gh CLI not found. Install: winget install GitHub.cli" -ForegroundColor Red
        }
    }

# --- 6. VS Code + Copilot ---
Write-Host "[6/6] VS Code Insiders ... " -NoNewline
$code = Get-Command "code-insiders" -ErrorAction SilentlyContinue
if ($code) {
    Write-Host "OK" -ForegroundColor Green
} else {
    $codeStable = Get-Command "code" -ErrorAction SilentlyContinue
    if ($codeStable) {
        Write-Host "stable version found (Insiders recommended)" -ForegroundColor Yellow
    } else {
        Write-Host "NOT FOUND" -ForegroundColor Red
        $install = Read-Host "       Install VS Code Insiders now? (y/n)"
        if ($install -eq 'y') {
            Write-Host "       Installing VS Code Insiders via winget..." -ForegroundColor Cyan
            winget install Microsoft.VisualStudioCode.Insiders --accept-source-agreements --accept-package-agreements 2>&1
            Write-Host "       Done." -ForegroundColor Green
        } else {
            Write-Host "       Manual: winget install Microsoft.VisualStudioCode.Insiders" -ForegroundColor Yellow
        }
        $allGood = $false
    }
}

# --- MCP Config ---
Write-Host ""
Write-Host "--- MCP Configuration ---" -ForegroundColor Yellow
$mcpTarget = "$env:USERPROFILE\.copilot\mcp-config.json"
if (Test-Path $mcpTarget) {
    Write-Host "  mcp-config.json exists at $mcpTarget" -ForegroundColor Green
    $overwrite = Read-Host "  Overwrite with template? (y/n)"
    if ($overwrite -eq 'y') {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        Copy-Item "$scriptDir\mcp-config.template.json" $mcpTarget -Force
        Write-Host "  Updated mcp-config.json" -ForegroundColor Green
    } else {
        Write-Host "  Kept existing config" -ForegroundColor Green
    }
} else {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $templatePath = "$scriptDir\mcp-config.template.json"
    if (Test-Path $templatePath) {
        Copy-Item $templatePath $mcpTarget -Force
        Write-Host "  Created mcp-config.json from template" -ForegroundColor Green
    } else {
        Write-Host "  No template found, you need to create mcp-config.json manually" -ForegroundColor Yellow
    }
}

# --- Summary ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host " All core prerequisites met!" -ForegroundColor Green
} else {
    Write-Host " Some prerequisites missing (see above)" -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run .\Install-MaoQiuQiu.ps1 to install agents"
Write-Host "  2. Run: az login (if not logged in)"
Write-Host "  3. Open VS Code Insiders, type @lduan-agent in Copilot Chat"
Write-Host ""
