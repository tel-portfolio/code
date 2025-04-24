# Connect to Microsoft Graph
Connect-MgGraph -Scopes "User.ReadWrite.All"

# Get user.csv file
$rows = Import-Csv -Path "./users.csv"

# Sort Groups
# $groups = $($row.Group)

foreach ($row in $rows) {

    $userUPN = $($row.UserPrinicpalName)
    $groups = $($row.Group)

    Write-Host "--- New User ---"

    Write-Host "Name: $($row.DisplayName)"
    Write-Host "Email: $($row.UserPrinicalName)"
    Write-Host "Password: $($row.password)"
    Write-Host "Group: $($row.Group)"

}