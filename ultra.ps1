# Ultra-PC launcher — run from ANY directory.
#   ultra learn "how do plants make food"
#   ultra kb "photosynthesis"
#
# One-time setup (opens a new PowerShell first for it to take effect):
#   Set-Alias -Name ultra -Value "C:\Users\desmo\AI Programs\Ultra-PC\ultra.ps1" `
#     -Option AllScope -Scope Global
# Or add that line to your PowerShell profile ($PROFILE) to make it permanent.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
# Stay in the caller's directory so relative file args work (ultra md notes.md).
# ultra.bat finds Python and anchors its own paths to the script location.
& (Join-Path $root "ultra.bat") @args
exit $LASTEXITCODE
