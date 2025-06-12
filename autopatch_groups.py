import requests
import json

# Function to list all available Autopatch groups using Microsoft Graph API
# Requires: Group.Read.All or Group.ReadWrite.All permissions

def list_autopatch_groups(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Autopatch groups are typically managed via Intune or Windows Autopatch API endpoints
    # This example uses the Windows Autopatch API (beta) for managed tenants
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsAutopatch/managedTenants"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tenants = response.json().get('value', [])
    if not tenants:
        print("No Autopatch managed tenants found.")
        return
    print("Autopatch Managed Tenants:")
    for tenant in tenants:
        print(json.dumps(tenant, indent=2))

# Example usage:
# token = get_access_token()
# list_autopatch_groups(token)
