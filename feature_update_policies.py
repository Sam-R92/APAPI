import requests
import json

def list_feature_update_policies(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsFeatureUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    if not profiles:
        print("No Windows Feature Update Profiles found.")
        return
    print("Windows Feature Update Profiles:")
    for profile in profiles:
        print(json.dumps(profile, indent=2))

# Example usage:
# token = get_access_token()
# list_feature_update_policies(token)
