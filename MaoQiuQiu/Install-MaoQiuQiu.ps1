<#
.SYNOPSIS
    Install SQL DRI Copilot Agent to ~/.copilot/agents/
.DESCRIPTION
    Copies agent definitions, skills, and KQL templates to the VS Code Copilot agent directory.
    Safe to re-run — will not overwrite existing outcome/search-results/errorcode_research files.
.EXAMPLE
    .\Install-SqlDriCopilot.ps1
    .\Install-SqlDriCopilot.ps1 -TargetDir "D:\my-copilot\agents"
#>
param(
    [string]$TargetDir = "$env:USERPROFILE\.copilot\agents"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = $scriptDir

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MaoQiuQiu Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source:  $sourceDir"
Write-Host "Target:  $TargetDir"
Write-Host ""

# Create target if not exists
if (-not (Test-Path $TargetDir)) {
    New-Item $TargetDir -ItemType Directory -Force | Out-Null
    Write-Host "[+] Created $TargetDir" -ForegroundColor Green
}

# Copy agent definitions
Write-Host ""
Write-Host "--- Agent Definitions ---" -ForegroundColor Yellow
$agentFiles = Get-ChildItem $sourceDir -Filter "*.agent.md" -File
foreach ($f in $agentFiles) {
    Copy-Item $f.FullName "$TargetDir\$($f.Name)" -Force
    Write-Host "  [+] $($f.Name)"
}
Copy-Item "$sourceDir\README.md" "$TargetDir\README.md" -Force
Write-Host "  [+] README.md"

# Copy skills
Write-Host ""
Write-Host "--- Skills ---" -ForegroundColor Yellow
$skillsTarget = "$TargetDir\skills"
if (-not (Test-Path $skillsTarget)) { New-Item $skillsTarget -ItemType Directory -Force | Out-Null }

$skillFiles = @(
    "db-kql-investigation.md",
    "mi-kql-investigation.md",
    "nys-analysis.md",
    "pr-tracking.md",
    "report-rules.md"
)
foreach ($f in $skillFiles) {
    $src = "$sourceDir\skills\$f"
    if (Test-Path $src) {
        Copy-Item $src "$skillsTarget\$f" -Force
        Write-Host "  [+] skills/$f"
    }
}

# Copy ops
$opsTarget = "$skillsTarget\ops"
if (-not (Test-Path $opsTarget)) { New-Item $opsTarget -ItemType Directory -Force | Out-Null }
Get-ChildItem "$sourceDir\skills\ops" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName "$opsTarget\$($_.Name)" -Force
    Write-Host "  [+] skills/ops/$($_.Name)"
}

# Copy kql-templates
Write-Host ""
Write-Host "--- KQL Templates ---" -ForegroundColor Yellow
$tplTarget = "$skillsTarget\kql-templates"
if (Test-Path "$sourceDir\skills\kql-templates") {
    Copy-Item "$sourceDir\skills\kql-templates" $tplTarget -Recurse -Force
    
    # Count templates
    $miCount = 0; $dbCount = 0
    Get-ChildItem "$tplTarget\mi" -Filter "*.yaml" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $c = Get-Content $_.FullName -Raw
        $miCount += ([regex]::Matches($c, '(?m)^- id:\s*MI-')).Count
    }
    Get-ChildItem "$tplTarget\sqldb" -Filter "*.yaml" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $c = Get-Content $_.FullName -Raw
        $dbCount += ([regex]::Matches($c, '(?m)^- id:\s*DB-')).Count
    }
    Write-Host "  [+] MI templates: $miCount skills"
    Write-Host "  [+] DB templates: $dbCount skills"
    Write-Host "  [+] Shared cluster mappings"
}

# Create output directories (don't overwrite existing)
Write-Host ""
Write-Host "--- Output Directories ---" -ForegroundColor Yellow
@("outcome", "errorcode_research", "search-results") | ForEach-Object {
    $dir = "$TargetDir\$_"
    if (-not (Test-Path $dir)) {
        New-Item $dir -ItemType Directory -Force | Out-Null
        Write-Host "  [+] Created $_/"
    } else {
        Write-Host "  [=] $_/ already exists (preserved)"
    }
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " MaoQiuQiu Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Ensure MCP servers are configured in ~/.copilot/mcp.json"
Write-Host "     Required: csswiki, msdata, enghub, microsoft-learn, github-mcp-server, azure-mcp"
Write-Host "  2. Open VS Code and use @lduan-agent to start"
Write-Host "  3. See README.md for usage details"
Write-Host ""
Write-Host "MCP config example: https://eng.ms/docs/..."
Write-Host ""
