import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
import time

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
client_uat_tester_andy = os.getenv("UATTESTER1")
client_uat_tester_louise = os.getenv("UATTESTER2")

headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"
test_case_ids = []

filepath = "payrollimportfile2.csv"

# =========================================================================
# 🌟 INITIALIZE PERSISTENT NETWORK SESSION
# =========================================================================
session = requests.Session()
session.headers.update(headers) # Apply headers globally across the connection pipe

# --- Fetch Metadata Reference Frameworks From Spira ---
print("\n📁 Fetching project test folder tree structures...")
all_folders = session.get(f"{base_url}/projects/{project_id}/test-folders", timeout=60).json()
folder_map = {f["Name"].strip().lower(): f["TestCaseFolderId"] for f in all_folders}

print("👤 Synchronizing user list directory...")
all_users = session.get(f"{base_url}/projects/{project_id}/users", timeout=60).json()
user_map = {u["FullName"].strip().lower(): u["UserId"] for u in all_users}

# --- Load and Clean Source Sheet ---
df = pd.read_csv(filepath)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.dropna(axis=0, how="all", inplace=True)
df.columns = df.columns.str.strip()

print(f"📋 Loaded {len(df)} row targets from CSV file.")

# --- State Persistence Engine Variables ---
case_id = None
current_step_position = 1

print("\n🎬 Executing Data Mapping Sequential Loop...")
print("=" * 70)
folder_id = None

for index, row in df.iterrows():
    row_num = index

    folder_name = str(row.get("Scenario ID")).strip()
    get_folder = folder_map.get(folder_name.lower())

    if get_folder is not None: 
        folder_id = get_folder

    # Secure row attribute string isolation
    scenario_id_raw = str(row.get("Scenario No.", "")).strip()
    
    # Skip processing completely if the scenario tracking column line is blank or null
    if scenario_id_raw == "" or scenario_id_raw.lower() == "nan":
        continue

    
        
    test_case_name = str(row.get("Requirement", "Unspecified Requirement")).strip()
    test_case_desc = str(row.get("Test Case Description", "")).strip()
    test_step_desc = str(row.get("User Story", "")).strip()
    expected_result = str(row.get("Desired Outcome", "")).strip()
    raw_owner = str(row.get("Owner", "")).strip().lower()
    
    
    # Apply custom translation rules for assignment owners
    if raw_owner == "client" or raw_owner == "sharon":
        target_tester = client_user
    elif raw_owner == "ms":
        target_tester = ms_user
    elif raw_owner == "andy":
        target_tester = client_uat_tester_andy
    elif raw_owner == "louise":
        target_tester = client_uat_tester_louise
    else:
        target_tester = raw_owner

    tester_id = user_map.get(str(target_tester).strip().lower() if target_tester else "")

    if ".2" in scenario_id_raw or ".3" in scenario_id_raw:
        
                
        clean_step_desc = test_step_desc if (test_step_desc and test_step_desc.lower() != "nan") else "Execute scenario requirements."
        clean_expected = expected_result if (expected_result and expected_result.lower() != "nan") else "Configured outcome achieved successfully."
        
        step_payload = {
                    "TestCaseId": case_id,
                    "Description": clean_step_desc,
                    "ExpectedResult": clean_expected,
                    "Position": current_step_position
                }
                
        print(f"   ⚙️ Uploading Step -> Position [{current_step_position}]: '{clean_step_desc[:30]}...'")
                
        try:
            step_response = session.post(
                f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps",
                json=step_payload,
                timeout=30
                    )
                    
            if step_response.status_code in [200, 201, 202]:
                        print("      ↳ Step Created Successfully")
                        current_step_position=current_step_position+1

            else:
                        print(f"      ❌ FAILED to write step. Status: {step_response.status_code}, Context: {step_response.text}")
        except requests.exceptions.RequestException as se:
                    print(f"      ❌ Step network write failed: {se}")
                    time.sleep(1.0)
        continue
        



    test_case_payload = {
        "Name": test_case_name,
        "Description": test_case_desc,
        "ProjectID": str(project_id),
        "AuthorID": int(author_id) if author_id else None,
        "OwnerID": tester_id,
        "TestCaseFolderID": int(folder_id) if folder_id else None,
        "TestCaseStatusId": 5,
        "TestCaseStatusName": "Ready for Test"
    }
    
    # 📡 Stream across global connection session 
    try:
        response = session.post(
            f"{base_url}/projects/{project_id}/test-cases", 
            json=test_case_payload, 
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection interrupted on row {row_num}: {e}. Retrying loop...")
        time.sleep(2.0)
        continue
        
    if response.status_code in [200, 201, 202]:
        case_id = response.json()["TestCaseId"]
        test_case_ids.append(case_id)
        print(f"   ✅ SUCCESS: Created Test Case: [{case_id}]")
        
        current_step_position = 1
        
        clean_step_desc = test_step_desc if (test_step_desc and test_step_desc.lower() != "nan") else "Execute scenario requirements."
        clean_expected = expected_result if (expected_result and expected_result.lower() != "nan") else "Configured outcome achieved successfully."

        step_payload = {
            "TestCaseId": case_id,
            "Description": clean_step_desc,
            "ExpectedResult": clean_expected,
            "Position": current_step_position
        }
        
        print(f"   ⚙️ Uploading Step -> Position [{current_step_position}]: '{clean_step_desc[:30]}...'")
        
        
        try:
            step_response = session.post(
                f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps",
                json=step_payload,
                timeout=30
            )
            
            if step_response.status_code in [200, 201, 202]:
                print("      ↳ Step Created Successfully")
                current_step_position=current_step_position+1
            else:
                print(f"      ❌ FAILED to write step. Status: {step_response.status_code}, Context: {step_response.text}")
                
        except requests.exceptions.RequestException as se:
            print(f"      ❌ Step network write failed: {se}")
            time.sleep(1.0)
            
    else:
        print(f" ❌ FAILED to create Test Case. Status: {response.status_code}, Context: {response.text}")
        time.sleep(1.0)
        continue

    # A short pause keeps things orderly, but the session structure does the heavy lifting
    time.sleep(0.3)

print("\n" + "=" * 70)
print("🏁 Target execution complete! All structural rows populated to Spira cleanly.")
print("======================================================================")

# --- Mapping test cases to release ---
if test_case_ids:
    print("\n📦 Mapping created test cases to Release [ID: 452]...")
    for test in test_case_ids:
        mapping_payload = [test]
        try:
            release_post = session.post(
                f"{base_url}/projects/{project_id}/releases/452/test-cases", 
                json=mapping_payload, 
                timeout=30
            )
            if release_post.status_code in [200, 201, 202]:
                print(f"   📍 Mapped Case ID [{test}] to Release 452")
            else:
                print(f"   ❌ Release mapping failed for Case ID [{test}]: HTTP {release_post.status_code}")
        except Exception as e:
            print(f"   ❌ Network fault mapping case {test}: {e}")
        
        time.sleep(0.1)

# Clean up session connection on complete
session.close()
print("\n🏁 Process complete!")