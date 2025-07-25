# ============================================================================
# Windows Update Deployment Agent (Microsoft Graph API Automation Script)
#
# Description:
#   Automates management and deployment of Windows Update, Expedite, Hotpatch,
#   and Autopatch policies using Microsoft Graph API.
#   Supports listing, creating, deploying, modifying, and removing update policies
#   and assignments for Windows devices in Azure AD.
#
# Disclaimer:
#   This script is provided as-is without warranty of any kind. Use at your own risk.
#   Ensure you have the necessary Microsoft Graph API permissions and admin consent
#   before running this script in a production environment.
#
# Author: Sabarimani Ramalingam
# ============================================================================

"""
Windows Update Deployment Agent (apapi.py)

This script provides a command-line interface for managing Windows Update deployment, expedite, hotpatch, and related policies via Microsoft Graph API.

Author: Sabarimani Ramalingam
Date: June 2025

Disclaimer:
This script is provided as-is without warranty of any kind. Use at your own risk. Ensure you have the necessary permissions and have reviewed the code before running in a production environment.
"""

import requests
import json
from textwrap import wrap

TENANT_ID = 'cf4b33d5-05ec-4cc0-a302-b6a710f2ac60'
CLIENT_ID = '1810ae5f-2a36-4098-ac0e-7aac7471b801'
CLIENT_SECRET = 'qxr8Q~B-LCHlI-bV.C5bVUU9yutD86HVlIElEdxw'

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "https://graph.microsoft.com/.default"

def get_access_token():
    data = {
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(AUTHORITY, data=data)
    if response.status_code != 200:
        print("Error response from Azure AD:", response.text)
    response.raise_for_status()
    return response.json()['access_token']

def list_expedite_quality_updates(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    if not profiles:
        print("No Windows Quality Update Profiles found.")
        return
    # Sort by displayName
    profiles.sort(key=lambda x: x.get('displayName', ''))
    print(f"{'Display Name':35} | {'Expedited Update Settings':40} | {'Created Date':20}")
    print("-"*105)
    for profile in profiles:
        display_name = profile.get('displayName', '-')[:35]
        expedited_settings = profile.get('expeditedUpdateSettings', {})
        if expedited_settings:
            # Format as JSON string for compact display
            settings_str = json.dumps(expedited_settings, separators=(',', ':'))
        else:
            settings_str = '-'
        created = profile.get('createdDateTime', '-')
        print(f"{display_name:35} | {settings_str:40} | {created:20}")

def get_recent_quality_update(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = (
        "https://graph.microsoft.com/beta/admin/windows/updates/catalog/entries"
        "?$expand=microsoft.graph.windowsUpdates.qualityUpdateCatalogEntry/productRevisions"
        "&$orderby=releaseDateTime desc&$top=1"
    )
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    entries = data.get('value', [])
    if not entries:
        print("No recent quality update found.")
        return
    print("Most Recent Quality Update:")
    print(json.dumps(entries, indent=2))

def create_aad_group(access_token, group_name):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "displayName": group_name,
        "mailEnabled": False,
        "mailNickname": group_name.replace(' ', '').lower(),
        "securityEnabled": True,
        "groupTypes": []
    }
    url = "https://graph.microsoft.com/v1.0/groups"
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    group = response.json()
    print(f"Created Azure AD group: {group.get('displayName')} (ID: {group.get('id')})")
    return group.get('id')

def create_deployment_for_recent_update(access_token, update_id, group_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "content": {
            "catalogEntry": {
                "id": update_id
            }
        },
        "audience": {
            "azureADGroupIds": [group_id]
        },
        "settings": {
            "expedite": {
                "isExpedited": True,
                "isReadinessTest": False
            },
            "userExperience": {
                "daysUntilForcedReboot": 2
            }
        }
    }
    url = "https://graph.microsoft.com/beta/admin/windows/updates/deployments"
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("Create deployment response:", response.text)
    response.raise_for_status()
    print("Deployment for recent quality update created successfully.")

def get_existing_groups(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/v1.0/groups?$select=id,displayName&$top=20"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    groups = response.json().get('value', [])
    return groups

def list_all_devices(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/v1.0/devices?$select=displayName,deviceId,managementType,operatingSystemVersion"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    devices = response.json().get('value', [])
    if not devices:
        print("No devices found.")
        return
    print("Devices:")
    for device in devices:
        print(f"Name: {device.get('displayName')}, ID: {device.get('deviceId')}, Management: {device.get('managementType')}, OS Version: {device.get('operatingSystemVersion')}")

def list_feature_update_options(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = ("https://graph.microsoft.com/beta/admin/windows/updates/catalog/entries"
           "?$filter=isof('microsoft.graph.windowsUpdates.featureUpdateCatalogEntry')")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    entries = data.get('value', [])
    if not entries:
        print("No feature update catalog entries found.")
        return
    print("Feature Update Options:")
    for entry in entries:
        print(json.dumps(entry, indent=2))

def deploy_feature_update(access_token):
    # Step 1: List all available feature updates
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = ("https://graph.microsoft.com/beta/admin/windows/updates/catalog/entries"
           "?$filter=isof('microsoft.graph.windowsUpdates.featureUpdateCatalogEntry')")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    entries = data.get('value', [])
    if not entries:
        print("No feature update catalog entries found.")
        return
    print("Available Feature Updates:")
    for idx, entry in enumerate(entries, 1):
        print(f"{idx}. Title: {entry.get('title', 'N/A')} | ID: {entry.get('id')}")
    # Step 2: Ask user to choose a version
    while True:
        sel = input("Enter the number of the feature update to deploy: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(entries):
            feature_update = entries[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    update_id = feature_update.get('id')
    # Step 3: Ask for Azure AD group
    use_existing = input("Do you want to use an existing Azure AD group? (yes/no): ").strip().lower()
    if use_existing in ("yes", "y"):
        try:
            groups = get_existing_groups(access_token)
            if not groups:
                print("No groups found. You must create a new group.")
                use_existing = "no"
            else:
                print("Available groups:")
                for idx, g in enumerate(groups, 1):
                    print(f"{idx}. {g['displayName']} (ID: {g['id']})")
                while True:
                    sel = input("Enter the number of the group to use, or type the group ID directly: ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(groups):
                        group_id = groups[int(sel)-1]['id']
                        break
                    elif any(g['id'] == sel for g in groups):
                        group_id = sel
                        break
                    else:
                        print("Invalid selection. Try again.")
        except Exception as e:
            print(f"Failed to list groups: {e}")
            return
    if use_existing not in ("yes", "y"):
        while True:
            group_name = input("Enter Azure AD group name to create for deployment: ").strip()
            if not group_name:
                print("Group name cannot be empty.")
                continue
            try:
                group_id = create_aad_group(access_token, group_name)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print("ERROR: 403 Forbidden. Your app registration likely lacks Group.ReadWrite.All (application) permission.\n"\
                          "Please grant this permission and admin consent in Azure AD, then try again.")
                    return
                else:
                    print(f"Failed to create group: {e}")
                    return
    # Step 4: Deploy the selected feature update
    payload = {
        "content": {
            "catalogEntry": {
                "@odata.type": "#microsoft.graph.windowsUpdates.featureUpdateCatalogEntry",
                "id": update_id
            }
        },
        "audience": {
            "azureADGroupIds": [group_id]
        },
        "settings": {
            "@odata.type": "#microsoft.graph.windowsUpdates.deploymentSettings",
            "schedule": {
                "startDateTime": "2025-06-10T05:00:00Z",
                "gradualRollout": {
                    "@odata.type": "#microsoft.graph.windowsUpdates.rateDrivenRolloutSettings",
                    "durationBetweenOffers": "P3D",
                    "devicesPerOffer": 100
                }
            },
            "monitoring": {
                "monitoringRules": [
                    {
                        "signal": "rollback",
                        "threshold": 5,
                        "action": "pauseDeployment"
                    }
                ]
            }
        }
    }
    deploy_url = "https://graph.microsoft.com/beta/admin/windows/updates/deployments"
    resp = requests.post(deploy_url, headers=headers, data=json.dumps(payload))
    print("Create feature update deployment response:", resp.text)
    resp.raise_for_status()
    print("Feature update deployment created successfully.")

def list_feature_update_policies(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsFeatureUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    # Filter for displayName containing 'Autopatch'
    autopatch_profiles = [p for p in profiles if 'Autopatch' in p.get('displayName', '')]
    if not autopatch_profiles:
        print("No Windows Feature Update Profiles with 'Autopatch' in the name found.")
        return
    # Sort by displayName
    autopatch_profiles.sort(key=lambda x: x.get('displayName', ''))
    # Print as table with createdDateTime
    print(f"{'Display Name':35} | {'Feature Update Version':20} | {'Created Date':20}")
    print("-"*85)
    for profile in autopatch_profiles:
        display_name = profile.get('displayName', '-')[:35]
        version = profile.get('featureUpdateVersion', '-')
        created = profile.get('createdDateTime', '-')
        print(f"{display_name:35} | {version:20} | {created:20}")

def list_driver_update_policies(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsDriverUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    # Filter for displayName containing 'Autopatch'
    autopatch_profiles = [p for p in profiles if 'Autopatch' in p.get('displayName', '')]
    if not autopatch_profiles:
        print("No Windows Driver Update Profiles with 'Autopatch' in the name found.")
        return
    # Sort by displayName
    autopatch_profiles.sort(key=lambda x: x.get('displayName', ''))
    # Print as table with createdDateTime and approvalType
    print(f"{'Display Name':35} | {'Approval Type':20} | {'Created Date':20}")
    print("-"*85)
    for profile in autopatch_profiles:
        display_name = profile.get('displayName', '-')[:35]
        approval_type = profile.get('approvalType', '-')
        created = profile.get('createdDateTime', '-')
        print(f"{display_name:35} | {approval_type:20} | {created:20}")

def list_hotpatch_policies(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    policies = response.json().get('value', [])
    if not policies:
        print("No Windows Quality Update Policies found.")
        return
    # Sort by displayName
    policies.sort(key=lambda x: x.get('displayName', ''))
    # Print as table with createdDateTime and hotpatchEnabled
    print(f"{'Display Name':35} | {'Hotpatch Enabled':15} | {'Created Date':20}")
    print("-"*80)
    for policy in policies:
        display_name = policy.get('displayName', '-')[:35]
        hotpatch_enabled = str(policy.get('hotpatchEnabled', '-'))
        created = policy.get('createdDateTime', '-')
        print(f"{display_name:35} | {hotpatch_enabled:15} | {created:20}")

def create_expedite_quality_update(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Step 1: List up to 4 available expedite quality updates
    url = ("https://graph.microsoft.com/beta/admin/windows/updates/catalog/entries"
           "?$filter=isof('microsoft.graph.windowsUpdates.qualityUpdateCatalogEntry') "
           "and microsoft.graph.windowsUpdates.qualityUpdateCatalogEntry/isExpeditable eq true"
           "&$orderby=releaseDateTime desc&$top=4")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    updates = response.json().get('value', [])
    if not updates:
        print("No expedite quality updates available.")
        return
    print("Available Expedite Quality Updates:")
    for idx, update in enumerate(updates, 1):
        display_name = update.get('displayName', '-')
        release_date = update.get('releaseDateTime', '-')
        print(f"{idx}. Name: {display_name[:40]} | Release Date: {release_date}")
    print("5. Cancel")
    # Step 2: Ask user to select one or cancel
    while True:
        sel = input("Enter the number of the expedite update to use (or 5 to cancel): ").strip()
        if sel == '5':
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(updates):
            selected_update = updates[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    update_id = selected_update.get('id')
    # Step 3: Ask for profile name
    profile_name = input("Enter a name for the new Expedite Quality Update profile: ").strip()
    if not profile_name:
        print("Profile name cannot be empty.")
        return
    # Step 4: Create the profile
    payload = {
        "displayName": profile_name,
        "expeditedUpdateSettings": {
            "qualityUpdateRelease": selected_update.get('releaseDateTime'),
            "daysUntilForcedReboot": 1
        }
    }
    create_url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles"
    resp = requests.post(create_url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 201:
        print(f"Expedite Quality Update profile '{profile_name}' created successfully.")
    else:
        print(f"Failed to create profile: {resp.status_code} {resp.text}")

def deploy_expedite_quality_update(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Step 1: List available expedite quality update profiles
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    if not profiles:
        print("No Expedite Quality Update Profiles found. Please create one first.")
        return
    print("Available Expedite Quality Update Profiles:")
    print(f"{'No.':3} {'Display Name':40} | {'Expedite Update Settings':40} | {'Created':20}")
    print("-"*110)
    for idx, profile in enumerate(profiles, 1):
        display_name = profile.get('displayName', '-')[:40]
        created = profile.get('createdDateTime', '-')
        expedited_settings = profile.get('expeditedUpdateSettings', {})
        if expedited_settings:
            settings_str = json.dumps(expedited_settings, separators=(',', ':'))
        else:
            settings_str = '-'
        print(f"{idx:3} {display_name:40} | {settings_str:40} | {created:20}")
    cancel_option = len(profiles) + 1
    print(f"{cancel_option}. Cancel")
    # Step 2: Ask user to select a profile or cancel
    while True:
        sel = input(f"Enter the number of the Expedite Quality Update profile to deploy (or {cancel_option} to cancel): ").strip()
        if sel == str(cancel_option):
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(profiles):
            selected_profile = profiles[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    profile_id = selected_profile.get('id')
    # Step 3: Ask for group deployment method
    use_existing = input("Do you want to use an existing Azure AD group? (yes/no): ").strip().lower()
    if use_existing in ("yes", "y"):
        groups = get_existing_groups(access_token)
        if not groups:
            print("No groups found. You must create a new group.")
            use_existing = "no"
        else:
            print("Available groups:")
            for idx, g in enumerate(groups, 1):
                print(f"{idx}. {g['displayName']} (ID: {g['id']})")
            while True:
                sel = input("Enter the number of the group to use, or type the group ID directly: ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(groups):
                    group_id = groups[int(sel)-1]['id']
                    break
                elif any(g['id'] == sel for g in groups):
                    group_id = sel
                    break
                else:
                    print("Invalid selection. Try again.")
    if use_existing not in ("yes", "y"):
        while True:
            group_name = input("Enter Azure AD group name to create for deployment: ").strip()
            if not group_name:
                print("Group name cannot be empty.")
                continue
            try:
                group_id = create_aad_group(access_token, group_name)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print("ERROR: 403 Forbidden. Your app registration likely lacks Group.ReadWrite.All (application) permission.\n"
                          "Please grant this permission and admin consent in Azure AD, then try again.")
                    return
                else:
                    print(f"Failed to create group: {e}")
                    return
    # Step 4: Assign the profile to the group
    assign_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles/{profile_id}/assignments"
    payload = {
        "assignments": [
            {
                "target": {
                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                    "groupId": group_id
                }
            }
        ]
    }
    resp = requests.post(assign_url, headers=headers, data=json.dumps(payload))
    if resp.status_code in (200, 201, 204):
        print("Expedite quality update profile assigned to group successfully.")
    else:
        print(f"Failed to assign profile: {resp.status_code} {resp.text}")

def list_configuration_policies(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/configurationPolicies"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    policies = response.json().get('value', [])
    autopatch_policies = [p for p in policies if 'Autopatch' in p.get('name', '')]
    if not autopatch_policies:
        print("No Configuration Policies with 'Autopatch' in the name found.")
        return
    autopatch_policies.sort(key=lambda x: x.get('name', ''))
    print(f"{'Policy Name':40} | {'Description':40} | {'Created Date':20}")
    print("-"*110)
    for policy in autopatch_policies:
        name = policy.get('name', '-')
        description = policy.get('description', '-')
        created = policy.get('createdDateTime', '-')
        name_lines = wrap(name, 40) or ['-']
        desc_lines = wrap(description, 40) or ['-']
        max_lines = max(len(name_lines), len(desc_lines))
        for i in range(max_lines):
            n = name_lines[i] if i < len(name_lines) else ''
            d = desc_lines[i] if i < len(desc_lines) else ''
            c = created if i == 0 else ''
            print(f"{n:40} | {d:40} | {c:20}")

def removal(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    print("Removal Menu:")
    print("1. Remove assignment from a policy")
    print("2. Delete a policy")
    print("3. Cancel")
    choice = input("Enter your choice (1-3): ").strip()
    if choice == '3':
        print("Operation cancelled.")
        return
    if choice not in ('1', '2'):
        print("Invalid choice.")
        return
    # List all policies (expedite and hotpatch)
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    expedite_profiles = response.json().get('value', [])
    url2 = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies"
    response2 = requests.get(url2, headers=headers)
    response2.raise_for_status()
    hotpatch_policies = response2.json().get('value', [])
    all_policies = [(p.get('id'), p.get('displayName', '-') + ' (Expedite)', 'expedite') for p in expedite_profiles]
    all_policies += [(p.get('id'), p.get('displayName', '-') + ' (Hotpatch)', 'hotpatch') for p in hotpatch_policies]
    if not all_policies:
        print("No policies found.")
        return
    print("Available Policies:")
    for idx, (_, name, typ) in enumerate(all_policies, 1):
        print(f"{idx}. {name}")
    cancel_option = len(all_policies) + 1
    print(f"{cancel_option}. Cancel")
    while True:
        sel = input(f"Select a policy (or {cancel_option} to cancel): ").strip()
        if sel == str(cancel_option):
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(all_policies):
            selected_id, selected_name, selected_type = all_policies[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again or select Cancel.")
    if choice == '1':
        # Remove assignment
        # List assignments for the selected policy
        if selected_type == 'expedite':
            assign_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles/{selected_id}/assignments"
        else:
            assign_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies/{selected_id}/assignments"
        resp = requests.get(assign_url, headers=headers)
        resp.raise_for_status()
        assignments = resp.json().get('value', [])
        if not assignments:
            print("No assignments found for this policy.")
            return
        # Collect all group IDs from assignments
        group_ids = [a.get('target', {}).get('groupId', '-') for a in assignments if a.get('target', {}).get('groupId')]
        group_id_to_name = {}
        if group_ids:
            # Batch fetch group names from Azure AD
            # Microsoft Graph allows $filter for up to 15 IDs per request
            batch_size = 15
            for i in range(0, len(group_ids), batch_size):
                batch = group_ids[i:i+batch_size]
                filter_str = ' or '.join([f"id eq '{gid}'" for gid in batch])
                groups_url = f"https://graph.microsoft.com/v1.0/groups?$select=id,displayName&$filter={filter_str}"
                groups_resp = requests.get(groups_url, headers=headers)
                if groups_resp.status_code == 200:
                    groups = groups_resp.json().get('value', [])
                    for g in groups:
                        group_id_to_name[g['id']] = g.get('displayName', g['id'])
                else:
                    # If the batch fails, fallback to group ID
                    for gid in batch:
                        group_id_to_name[gid] = gid
        print("Assignments:")
        for idx, a in enumerate(assignments, 1):
            group_id = a.get('target', {}).get('groupId', '-')
            group_name = group_id_to_name.get(group_id, group_id) if group_id != '-' else '-'
            print(f"{idx}. Group: {group_name} (ID: {group_id})")
        cancel_assign = len(assignments) + 1
        print(f"{cancel_assign}. Cancel")
        while True:
            sel = input(f"Select an assignment to remove (or {cancel_assign} to cancel): ").strip()
            if sel == str(cancel_assign):
                print("Operation cancelled.")
                return
            if sel.isdigit() and 1 <= int(sel) <= len(assignments):
                assignment_id = assignments[int(sel)-1]['id']
                break
            else:
                print("Invalid selection. Try again or select Cancel.")
        # Remove assignment
        if selected_type == 'expedite':
            del_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles/{selected_id}/assignments/{assignment_id}"
            del_resp = requests.delete(del_url, headers=headers)
            if del_resp.status_code in (200, 204):
                print("Assignment removed successfully.")
            else:
                print(f"Failed to remove assignment: {del_resp.status_code} {del_resp.text}")
        else:
            print("Assignment removal for Hotpatch policies is not supported via Microsoft Graph API. You may need to delete and recreate the policy if you wish to change assignments.")
    elif choice == '2':
        # Delete policy
        confirm = input(f"Are you sure you want to delete policy '{selected_name}'? Type 'yes' to confirm: ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        if selected_type == 'expedite':
            del_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles/{selected_id}"
        else:
            del_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies/{selected_id}"
        del_resp = requests.delete(del_url, headers=headers)
        if del_resp.status_code in (200, 204):
            print("Policy deleted successfully.")
        else:
            print(f"Failed to delete policy: {del_resp.status_code} {del_resp.text}")

def create_hotpatch_policy(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    print("\nCreate Hotpatch Policy:")
    policy_name = input("Enter a name for the new Hotpatch Policy: ").strip()
    if not policy_name:
        print("Policy name cannot be empty.")
        return
    enable_hotpatch = input("Enable hotpatch? (yes/no): ").strip().lower()
    if enable_hotpatch not in ("yes", "y", "no", "n"):
        print("Invalid input. Please enter 'yes' or 'no'.")
        return
    hotpatch_enabled = enable_hotpatch in ("yes", "y")
    payload = {
        "displayName": policy_name,
        "hotpatchEnabled": hotpatch_enabled
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies"
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 201:
        print(f"Hotpatch Policy '{policy_name}' created successfully.")
    else:
        print(f"Failed to create Hotpatch Policy: {response.status_code} {response.text}")

def deploy_hotpatch_policy(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    policies = response.json().get('value', [])
    if not policies:
        print("No Hotpatch Policies found.")
        return
    print("Available Hotpatch Policies:")
    for idx, policy in enumerate(policies, 1):
        print(f"{idx}. {policy.get('displayName', '-')[:40]} (ID: {policy.get('id')})")
    print(f"{len(policies)+1}. Cancel")
    while True:
        sel = input(f"Select a policy to assign to a group (1-{len(policies)+1}): ").strip()
        if sel == str(len(policies)+1):
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(policies):
            selected_policy = policies[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    policy_id = selected_policy.get('id')
    use_existing = input("Do you want to use an existing Azure AD group? (yes/no): ").strip().lower()
    if use_existing in ("yes", "y"):
        groups = get_existing_groups(access_token)
        if not groups:
            print("No groups found. You must create a new group.")
            use_existing = "no"
        else:
            print("Available groups:")
            for idx, g in enumerate(groups, 1):
                print(f"{idx}. {g['displayName']} (ID: {g['id']})")
            while True:
                sel = input("Enter the number of the group to use, or type the group ID directly: ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(groups):
                    group_id = groups[int(sel)-1]['id']
                    break
                elif any(g['id'] == sel for g in groups):
                    group_id = sel
                    break
                else:
                    print("Invalid selection. Try again.")
    if use_existing not in ("yes", "y"):
        while True:
            group_name = input("Enter Azure AD group name to create for deployment: ").strip()
            if not group_name:
                print("Group name cannot be empty.")
                continue
            try:
                group_id = create_aad_group(access_token, group_name)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print("ERROR: 403 Forbidden. Your app registration likely lacks Group.ReadWrite.All (application) permission.\n"
                          "Please grant this permission and admin consent in Azure AD, then try again.")
                    return
                else:
                    print(f"Failed to create group: {e}")
                    return
    # Assign the hotpatch policy to the group (single assignment object)
    assign_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies/{policy_id}/assignments"
    payload = {
        "target": {
            "@odata.type": "#microsoft.graph.groupAssignmentTarget",
            "groupId": group_id
        }
    }
    resp = requests.post(assign_url, headers=headers, data=json.dumps(payload))
    if resp.status_code in (200, 201, 204):
        print("Hotpatch policy assigned to group successfully.")
    else:
        print(f"Failed to assign hotpatch policy: {resp.status_code} {resp.text}")

def modify_expedite_policy(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json().get('value', [])
    if not profiles:
        print("No Expedite Quality Update Profiles found.")
        return
    print("Available Expedite Quality Update Profiles:")
    for idx, profile in enumerate(profiles, 1):
        print(f"{idx}. {profile.get('displayName', '-')[:40]} (ID: {profile.get('id')})")
    print(f"{len(profiles)+1}. Cancel")
    while True:
        sel = input(f"Select a profile to modify (1-{len(profiles)+1}): ").strip()
        if sel == str(len(profiles)+1):
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(profiles):
            selected_profile = profiles[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    profile_id = selected_profile.get('id')
    print(f"Selected: {selected_profile.get('displayName', '-')}")
    print("Current expeditedUpdateSettings:")
    print(json.dumps(selected_profile.get('expeditedUpdateSettings', {}), indent=2))
    new_days = input("Enter new 'daysUntilForcedReboot' (leave blank to keep current): ").strip()
    expedited_settings = selected_profile.get('expeditedUpdateSettings', {})
    if new_days:
        try:
            expedited_settings['daysUntilForcedReboot'] = int(new_days)
        except ValueError:
            print("Invalid number. Keeping current value.")
    patch_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdateProfiles/{profile_id}"
    payload = {"expeditedUpdateSettings": expedited_settings}
    patch_resp = requests.patch(patch_url, headers=headers, data=json.dumps(payload))
    if patch_resp.status_code in (200, 204):
        print("Profile updated successfully.")
    else:
        print(f"Failed to update profile: {patch_resp.status_code} {patch_resp.text}")

def modify_hotpatch_policy(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    policies = response.json().get('value', [])
    if not policies:
        print("No Hotpatch Policies found.")
        return
    print("Available Hotpatch Policies:")
    for idx, policy in enumerate(policies, 1):
        print(f"{idx}. {policy.get('displayName', '-')[:40]} (ID: {policy.get('id')})")
    print(f"{len(policies)+1}. Cancel")
    while True:
        sel = input(f"Select a policy to modify (1-{len(policies)+1}): ").strip()
        if sel == str(len(policies)+1):
            print("Operation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(policies):
            selected_policy = policies[int(sel)-1]
            break
        else:
            print("Invalid selection. Try again.")
    policy_id = selected_policy.get('id')
    print(f"Selected: {selected_policy.get('displayName', '-')}")
    print("Current hotpatchEnabled:", selected_policy.get('hotpatchEnabled', '-'))
    new_enabled = input("Enable hotpatch? (yes/no, leave blank to keep current): ").strip().lower()
    if new_enabled in ("yes", "y"):
        hotpatch_enabled = True
    elif new_enabled in ("no", "n"):
        hotpatch_enabled = False
    else:
        hotpatch_enabled = selected_policy.get('hotpatchEnabled', False)
    patch_url = f"https://graph.microsoft.com/beta/deviceManagement/windowsQualityUpdatePolicies/{policy_id}"
    payload = {"hotpatchEnabled": hotpatch_enabled}
    patch_resp = requests.patch(patch_url, headers=headers, data=json.dumps(payload))
    if patch_resp.status_code in (200, 204):
        print("Hotpatch policy updated successfully.")
    else:
        print(f"Failed to update hotpatch policy: {patch_resp.status_code} {patch_resp.text}")

def main():
    print("\nWelcome to the Windows Update Deployment Agent!")
    access_token = get_access_token()
    while True:
        print("\nWindows Update Deployment Agent - Main Menu:")
        print("1. List Expedite Quality Update Profiles")
        print("2. List Feature Update Policies (Autopatch)")
        print("3. List Driver Update Policies (Autopatch)")
        print("4. List Hotpatch Policies")
        print("5. List All Devices")
        print("6. Create Expedite Quality Update Profile")
        print("7. Deploy Expedite Quality Update Profile")
        print("8. Create Hotpatch Policy")
        print("9. Deploy Hotpatch Policy")
        print("10. Modify Expedite Quality Update Policy")
        print("11. Modify Hotpatch Policy")
        print("12. Remove Assignment or Delete Policy")
        print("13. List Configuration Policies (Autopatch)")
        print("14. Exit")
        choice = input("Select an option (1-14): ").strip()
        if choice == '1':
            list_expedite_quality_updates(access_token)
        elif choice == '2':
            list_feature_update_policies(access_token)
        elif choice == '3':
            list_driver_update_policies(access_token)
        elif choice == '4':
            list_hotpatch_policies(access_token)
        elif choice == '5':
            list_all_devices(access_token)
        elif choice == '6':
            create_expedite_quality_update(access_token)
        elif choice == '7':
            deploy_expedite_quality_update(access_token)
        elif choice == '8':
            create_hotpatch_policy(access_token)
        elif choice == '9':
            deploy_hotpatch_policy(access_token)
        elif choice == '10':
            modify_expedite_policy(access_token)
        elif choice == '11':
            modify_hotpatch_policy(access_token)
        elif choice == '12':
            removal(access_token)
        elif choice == '13':
            list_configuration_policies(access_token)
        elif choice == '14':
            print("Thank you for using the Windows Update Deployment Agent. Goodbye!")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    main()