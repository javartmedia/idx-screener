$server = "100.109.179.25"
$username = "kisai7"
$password = "Asdx!@327957"

# Create a temporary expect script
$expectScript = @"
spawn ssh -o StrictHostKeyChecking=no $username@$server
expect "password:"
send "$password\r"
expect "$ "
send "uname -a\r"
expect "$ "
send "exit\r"
"@

# Write the expect script to a temp file
$expectFile = "$env:TEMP\ssh_expect.exp"
$expectScript | Out-File -FilePath $expectFile -Encoding ASCII

Write-Host "SSH connection test script created at: $expectFile"
Write-Host ""
Write-Host "Note: You may need to install 'expect' tool for automated SSH."
Write-Host "Alternative: Use PuTTY's plink.exe or OpenSSH with SSH key authentication."
