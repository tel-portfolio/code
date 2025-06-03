# Connect to Microsoft Graph
Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All"

# Get user.csv file
$rows = Import-Csv -Path "./users.csv"

foreach ($row in $rows) {
    $userName = $($row.DisplayName)
    $userUPN = $($row.UserPrincipalName)
    $userGroup = $($row.Group)
    
    Write-Host "`n--- Processing User: $userName ---"
    Write-Host "Name: $($row.DisplayName)"
    Write-Host "Email: $($row.UserPrincipalName)"
    Write-Host "Group: $($row.Group)"
    
    try {
        # Create password profile
        $passwordProfile = @{
            Password = $row.password
            ForceChangePasswordNextSignIn = $false
        }
        
        # Create user object
        $newUser = @{
            DisplayName = $row.DisplayName
            UserPrincipalName = $row.UserPrincipalName
            AccountEnabled = $true
            PasswordProfile = $passwordProfile
            MailNickname = ($row.UserPrincipalName -split '@')[0]
        }
        
        # Create the user
        $createdUser = New-MgUser -BodyParameter $newUser
        Write-Host "✓ User created successfully with ID: $($createdUser.Id)" -ForegroundColor Green
        
        # Check if group exists, create if it doesn't
        $existingGroup = Get-MgGroup -Filter "displayName eq '$userGroup'" -ErrorAction SilentlyContinue
        
        if (-not $existingGroup) {
            Write-Host "Creating new group: $userGroup" -ForegroundColor Yellow
            $newGroup = @{
                DisplayName = $userGroup
                GroupTypes = @()
                MailEnabled = $false
                MailNickname = $userGroup -replace '\s',''
                SecurityEnabled = $true
            }
            $createdGroup = New-MgGroup -BodyParameter $newGroup
            $groupId = $createdGroup.Id
            Write-Host "✓ Group created successfully" -ForegroundColor Green
        } else {
            $groupId = $existingGroup.Id
            Write-Host "✓ Group already exists" -ForegroundColor Green
        }
        
        # Add user to group
        New-MgGroupMember -GroupId $groupId -DirectoryObjectId $createdUser.Id
        Write-Host "✓ User added to group successfully" -ForegroundColor Green
        
    }
    catch {
        Write-Host "✗ Failed to process user: $($_.Exception.Message)" -ForegroundColor Red
        continue
    }
}

Write-Host "`n--- Script completed ---"