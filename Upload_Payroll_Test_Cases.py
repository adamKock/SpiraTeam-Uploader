import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json

print("=== 🚀 Starting Scenario Pattern-Based Spira Uploader ===")

# --- Load Environment Variables ---
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
author_id = os.getenv("AUTH_ID")
base_url = os.getenv("SPIRA_URL")
ms_user = os.getenv("MS")
client_user = os.getenv("PAYROLL")


headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"

filepath = "GA_UK_Payroll Scenarios_11.05.26 - ST Copy AD.csv"

# --- Fetch Metadata Reference Frameworks From Spira ---
print("\n📁 Fetching project test folder tree structures...")
all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers).json()
folder_map = {f["Name"].strip().lower(): f["TestCaseFolderId"] for f in all_folders}

print("👤 Synchronizing user list directory...")
all_users = requests.get(f"{base_url}/projects/{project_id}/users", headers=headers).json()
user_map = {u["FullName"].strip().lower(): u["UserId"] for u in all_users}


# --- Load and Clean Source Sheet ---
df = pd.read_csv(filepath)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.dropna(axis=0, how="all", inplace=True)
df.columns = df.columns.str.strip()

print(f"📋 Loaded {len(df)} row targets from CSV file.")


# --- State Persistence Engine Variables (CRITICAL: Placed OUTSIDE Loop) ---
case_id = None
current_step_position = 1

print("\n🎬 Executing Data Mapping Sequential Loop...")
print("=" * 70)
folder_id = None


for index, row in df.iterrows():
    row_num =index

    folder_name = str(row.get("Requirement")).strip()
    get_folder = folder_map.get(folder_name.lower())

    if get_folder is not None: 
        folder_id = get_folder

    # Secure row attribute string isolation
    scenario_id_raw = str(row.get("Scenario No.", "")).strip()
    
    # Skip processing completely if the scenario tracking column line is blank or null
    if scenario_id_raw == "" or scenario_id_raw.lower() == "nan":
        continue
        
    test_case_name = str(row.get("Requirement", "Unspecified Requirement")).strip()
    test_step_desc = str(row.get("User Story", "")).strip()
    expected_result = str(row.get("Desired Outcome", "")).strip()
    raw_owner = str(row.get("Owner", "")).strip().lower()
    
    # Apply custom translation rules for assignment owners
    if raw_owner == "client":
        target_tester = client_user
    elif raw_owner == "ms":
        target_tester = ms_user
    else:
        target_tester = raw_owner

    tester_id = user_map.get(target_tester)

    # 🌟 RULE A: If scenario ID ends with .1, construct a brand new parent Test Case
    if scenario_id_raw.endswith(".1"):
        print("-" * 60)
        print(f"▶️ [Row {row_num}] New Test Case Boundary Found via ID: {scenario_id_raw}")
        print(f"   💡 Summary Name: '{test_case_name}'")
        
        # Reset tracking position index back to 1 for this test suite item
        current_step_position = 1
        case_id = None # Flush old index lookup reference
        
        test_case_payload = {
            "Name": test_case_name,
            "ProjectID": str(project_id),
            "AuthorID": int(author_id) if author_id else None,
            "OwnerID": tester_id,
            "TestCaseFolderID": int(folder_id) if folder_id else None,
        }
        
        response = requests.post(f"{base_url}/projects/{project_id}/test-cases", json=test_case_payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            case_id = response.json()["TestCaseId"]
            print(f"   ✅ SUCCESS: Created Test Case: [{case_id}]")
        else:
            print(f"   ❌ FAILED to create Test Case. Status: {response.status_code}, Context: {response.text}")
            continue

    # 🌟 RULE B: If it DOES NOT end with .1 (e.g., .2, .3), skip Test Case creation
    else:
        print(f"   ↳ [Row {row_num}] Step continuation row identified for ID: {scenario_id_raw}")

    # 🌟 BOTH paths flow down into this step uploader segment automatically
    if case_id is not None:
            
        step_payload = {
            "TestCaseId": case_id,
            "Description": test_step_desc,
            "ExpectedResult": expected_result if expected_result.lower() != "nan" else "",
            "Position": current_step_position
        }
        
        print(f"     ⚙️ Uploading Step to Position [{current_step_position}]...")
        step_url = f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps"
        step_response = requests.post(step_url, json=step_payload, headers=headers)
        
        if step_response.status_code in [200, 201, 202]:
            print(f"     ↳ ✅ Step {current_step_position} successfully added.")
            current_step_position += 1  # Increment sequential positions array safely for next loop item
        else:
            print(f"     ↳ ❌ FAILED to write step. Status Code: {step_response.status_code}")

print("\n" + "=" * 70)
print("🏁 Target execution complete! All structural rows populated to Spira cleanly.")
print("======================================================================")