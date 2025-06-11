# userAdd.ps1 — Quick‑Start

Bulk‑create Microsoft Entra ID (Azure AD) users from a CSV and put them in the right security groups.

## Prereqs
* PowerShell 7+  
* `Microsoft.Graph` PowerShell module  
  ```powershell
  Install-Module Microsoft.Graph -Scope CurrentUser

## CSV Layout
| DisplayName | UserPrincipalName                                   | Password  | MailNickname | Group |
| ----------- | --------------------------------------------------- | --------- | ------------ | ----- |
| Jane Doe    | [jane.doe@contoso.com](mailto:jane.doe@contoso.com) | Pass1234! | janed        | HR    |

## What Happens

    Connects to Graph (prompts if not already connected).

    For each CSV row:

        Skips if UPN exists.

        Creates user with supplied password.

        Creates target group if missing, then adds user.

    Errors go to error.log; progress shows with -Verbose.

    Disconnects from Graph.