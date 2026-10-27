# Copy this script between trusted operator computers; keep each private key local.
param(
    [Parameter(Mandatory = $true)][string]$Address,
    [string]$IdentityFile,
    [switch]$Admin
)
if ($Address -notmatch '^[a-zA-Z0-9.:_-]+$' -or $Address.StartsWith('-')) {
    Write-Error 'Enter a hostname or IP address without spaces or options.'
    exit 2
}
$sshArgs = @('-t', '-o', 'StrictHostKeyChecking=ask')
if ($IdentityFile) { $sshArgs += @('-i', $IdentityFile) }
$sshArgs += "devops@$Address"
if (-not $Admin) { $sshArgs += 'sudo -iu coder' }
& ssh @sshArgs
exit $LASTEXITCODE
