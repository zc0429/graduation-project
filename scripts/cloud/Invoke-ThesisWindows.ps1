# Use fonts only on the licensed hosted Windows machine. Never upload font files.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $repo
if (-not $env:THESIS_DELIVERY_ID) { throw 'THESIS_DELIVERY_ID is required' }
$run = Join-Path $repo "docs/validation/$env:THESIS_DELIVERY_ID"
New-Item -ItemType Directory -Force $run | Out-Null
Start-Transcript -Path (Join-Path $run 'windows-transcript.log')
try {
    python scripts/documents/thesis_windows_cloud.py inventory --output "$run/font-inventory-initial.json"
    $initial = Get-Content -Raw "$run/font-inventory-initial.json" | ConvertFrom-Json
    if (-not $initial.all_originals_available) {
        # Windows Update / Features on Demand is the official source; no fonts
        # are copied out of this machine, downloaded from font mirrors, or renamed.
        $componentJob = Start-Job -ScriptBlock {
            $ErrorActionPreference = 'Stop'
            Import-Module Dism
            $capabilities = Get-WindowsCapability -Online |
                Where-Object Name -like 'Language.Fonts.Hans*'
            $capabilities | Format-List Name, State
            if (-not $capabilities) { throw 'The hosted image exposes no Hans font capability' }
            foreach ($capability in $capabilities) {
                if ($capability.State -ne 'Installed') {
                    Add-WindowsCapability -Online -Name $capability.Name | Format-List
                }
            }
        }
        $completed = Wait-Job $componentJob -Timeout 360
        if (-not $completed) {
            Stop-Job $componentJob
            'Official optional-font installation exceeded 360 seconds' |
                Set-Content "$run/windows-optional-fonts.log"
        } else {
            Receive-Job $componentJob -ErrorAction Continue *>&1 |
                Out-String | Set-Content "$run/windows-optional-fonts.log"
        }
        Remove-Job $componentJob -Force
        # Broadcast WM_FONTCHANGE so subsequent fresh LibreOffice processes see it.
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class ThesisFontRefresh {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessageTimeout(IntPtr window, uint message,
        UIntPtr wparam, IntPtr lparam, uint flags, uint timeout, out UIntPtr result);
}
'@
        $result = [UIntPtr]::Zero
        [void][ThesisFontRefresh]::SendMessageTimeout([IntPtr]0xffff, 0x001d,
            [UIntPtr]::Zero, [IntPtr]::Zero, 2, 3000, [ref]$result)
    }
    python scripts/documents/thesis_windows_cloud.py inventory --output "$run/font-inventory.json"
    if ($LASTEXITCODE -ne 0) { throw 'Original Windows fonts remain unavailable; no formal PDF can be released' }

    $office = 'C:/Program Files/LibreOffice/program/soffice.com'
    if (-not (Test-Path $office)) {
        # The Chocolatey package validates the upstream MSI checksum. Do not
        # disable TLS or package checksums. Match the existing 25.2 renderer line.
        choco install libreoffice-fresh --version=25.2.3 --yes --no-progress 2>&1 |
            Tee-Object -FilePath "$run/libreoffice-install.log"
        if ($LASTEXITCODE -notin @(0, 3010)) { throw 'LibreOffice package installation failed' }
    }
    if (-not (Test-Path $office)) { throw 'LibreOffice console executable missing after installation' }
    python scripts/documents/thesis_windows_cloud.py render --office $office
    if ($LASTEXITCODE -ne 0) { throw 'Original-font rendering or document verification failed' }
} finally {
    Stop-Transcript
}

