import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
import time  # 🌟 Added to support the API throttle delay

load_dotenv()

api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
author_id = os.getenv("AUTH_ID")
base_url = os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id

filepath = "UAT - Compensation.csv"
test_case_ids = []
spira_id_tracker = {}  # Maps CSV 'Ref' -> Spira 'TestCaseId'
pending_prereqs = []   # Tracks test cases requiring a post-upload description update

df = pd.read_csv(filepath)

# Clean the DF 
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.dropna(axis=0, how="all", inplace=True)
df.columns = df.columns.str.strip()

# Get All the folders and users in the project with explicit timeouts
print("\n📡 Fetching folder cache and user maps from Spira...")
all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers, timeout=60).json()
folder_map = {f["Name"].strip().lower(): f["TestCaseFolderId"] for f in all_folders}

all_users = requests.get(f"{base_url}/projects/{project_id}/users", headers=headers, timeout=60).json()
user_map = {u["FullName"].strip().lower(): u["UserId"] for u in all_users}

case_id = None
current_step_position = 1

# Iterate through the csv creating the tests into the right folders 
for index, row in df.iterrows():
    row_num = index
    raw_tc_name = row.get("Test Case Name")
    is_new_test_case = (
        pd.notna(raw_tc_name) and 
        str(raw_tc_name).strip() != "" and 
        str(raw_tc_name).strip().lower() != "nan"
    )
    
    if is_new_test_case:
        print("-" * 60)
        tc_name = str(raw_tc_name).strip()
        
        # Reset step counters for a clean test case block
        current_step_position = 1
        
        process_group_name = str(row.get("Process Group", "")).strip().lower()
        actor_user = str(row.get("Actor / User", "")).strip().lower()
        tester_name = str(row.get("Tester", "")).strip().lower()
        
        folder_id = folder_map.get(process_group_name)
        tester_id = user_map.get(tester_name)
    
        raw_actor = row.get("Actor / User", "")
        actor_text = str(raw_actor).strip() if pd.notna(raw_actor) else ""
        base_description = (
            str(row.get("Test Case Description", ""))
            if pd.notna(row.get("Test Case Description"))
            else ""
        )

        if actor_text:
            combined_description = f"**Actor / User:** {actor_text}\n\n{base_description}"
        else:
            combined_description = base_description
        
        test_case_payload = {
            "Name": tc_name,
            "Description": str(combined_description),
            "ProjectID": str(project_id),
            "TestCaseFolderID": folder_id,
            "AuthorID": int(author_id) if author_id else None,
            "OwnerID": tester_id,
            "OwnerName": tester_name,
            "TestCaseStatusId": 5,
            "TestCaseStatusName": "Ready for Test"
        }
        
        # 🌟 TIMEOUT & FLOOD PROTECTION GATEWAY
        try:
            response = requests.post(
                f"{base_url}/projects/{project_id}/test-cases", 
                json=test_case_payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                case_id = response.json()["TestCaseId"]
                test_case_ids.append(case_id)
                print(f"✅ Created Test Case ID: [{case_id}] for Owner '{tester_name}'")
                
                csv_ref = str(row.get("Ref", "")).strip()
                if csv_ref and csv_ref.lower() != "nan":
                    spira_id_tracker[csv_ref] = case_id

                prereq_val = str(row.get("Prerequisites", "")).strip()
                if prereq_val and prereq_val.lower() != "nan":
                    pending_prereqs.append({
                        "target_spira_id": case_id,
                        "current_description": combined_description,
                        "prereq_csv_ref": prereq_val,
                    })
            else:
                print(f"❌ Server rejected Test Case definition. HTTP {response.status_code}")
                case_id = None

        except requests.exceptions.ConnectionError:
            print("⚠️ Connection closed by remote host. Pausing 3 seconds to recover gateway thresholds...")
            time.sleep(3.0)
            case_id = None
            continue
        
        # ⏱️ Throttle delay to protect security firewall layers
        time.sleep(0.4)
        
    else:
        if case_id is not None:
            print(f"   ↳ [Row {row_num}] Reading continuation steps for active Test Case ID [{case_id}]")

    # Loop through columns Step 1, 2, 3, 4
    if case_id is not None:
        csv_step_columns = ["Step 1", "Step 2", "Step 3", "Step 4"]

        for step_col in csv_step_columns:
            step_text = row.get(step_col)
            
            if pd.notna(step_text) and str(step_text).strip() != "" and str(step_text).strip().lower() != "nan":
                step_description = str(step_text).strip()
                expected_result = str(row.get("Expected Result", "")) if pd.notna(row.get("Expected Result")) else ""
                
                step_payload = {
                    "TestCaseId": case_id,
                    "Description": step_description,
                    "ExpectedResult": expected_result,
                    "Position": current_step_position
                }
                
                print(f"   ⚙️ Uploading Step -> Position [{current_step_position}]: '{step_description[:25]}...'")
                
                try:
                    step_response = requests.post(
                        f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps",
                        headers=headers,
                        json=step_payload,
                        timeout=30
                    )
                    
                    if step_response.status_code in [200, 201, 202]:
                        current_step_position += 1
                    else:
                        print(f"     ❌ FAILED to write step. Status: {step_response.status_code}")
                except Exception as e:
                    print(f"     ❌ Step network dropped: {e}")
                
                # ⏱️ Keep the steps from flooding back-to-back too fast
                time.sleep(0.2)

print("\n" + "=" * 60)
print("🏁 Core structural upload complete! Moving to relational mappings...")

# =========================================================================
# ⚡ Phase 2: Processing Prerequisite dependencies (FIXED)
# =========================================================================
if pending_prereqs:
    print("\n" + "=" * 60 + "\n⚡ Processing Prerequisite dependencies (Phase 2)...")
    for target in pending_prereqs:
        target_id = target["target_spira_id"]
        prereq_ref = target["prereq_csv_ref"]

        if prereq_ref in spira_id_tracker:
            prereq_spira_id = spira_id_tracker[prereq_ref]

            get_url = f"{base_url}/projects/{project_id}/test-cases/{target_id}"
            
            try:
                get_res = requests.get(get_url, headers=headers, timeout=30)
                
                if get_res.status_code == 200:
                    tc_data = get_res.json()
                    
                    # Update description properties safely
                    prereq_text = f"\n\n**Prerequisite Test Case ID:** {prereq_spira_id}"
                    tc_data["Description"] = f"{tc_data.get('Description', '')}{prereq_text}"

                    put_url = f"{base_url}/projects/{project_id}/test-cases"
                    
                    # Try the standard text update
                    update_res = requests.put(put_url, json=tc_data, headers=headers, timeout=30)

                    if update_res.status_code in [200, 204]:
                        print(f"🔗 Appended Prerequisite ID {prereq_spira_id} to Spira ID {target_id}")
                    else:
                        print(f"❌ Put update failed with status {update_res.status_code}, trying link fallback...")
                        raise requests.exceptions.ConnectionError
                        
            except (requests.exceptions.ConnectionError, Exception):
                # 🌟 FALLBACK LINK SYSTEM: If the server aborts the heavy PUT request,
                # use Spira's clean endpoint to link them without altering text structures
                print(f"   ↳ 🛡️ PUT aborted by host for ID {target_id}. Running link fallback system...")
                
                link_payload = {
                    "ArtifactId": target_id,
                    "ArtifactTypeId": 2,      # 2 is the system identifier for Test Cases
                    "LinkedArtifactId": prereq_spira_id,
                    "LinkedArtifactTypeId": 2,
                    "ArtifactLinkTypeId": 1   # 1 represents a standard Prerequisite block link
                }
                
                try:
                    link_res = requests.post(
                        f"{base_url}/projects/{project_id}/artifact-links",
                        json=link_payload,
                        headers=headers,
                        timeout=30
                    )
                    if link_res.status_code in [200, 201, 202]:
                        print(f"   ✅ Fallback Link Success: Connected {target_id} directly to prerequisite {prereq_spira_id}")
                    else:
                        print(f"   ❌ Fallback Link Rejected: HTTP {link_res.status_code}")
                except Exception as le:
                    print(f"   ❌ Fallback connection fault: {le}")

        else:
            print(f"⚠️ Prerequisite lookup failed for row referencing '{prereq_ref}'")
            
        # ⏱️ Small pause between updates to maintain server connection limits
        time.sleep(0.5)

# Phase 3: Map to Release Bundle Container
if test_case_ids:
    print("\n" + "=" * 60 + "\n📦 Mapping created test cases to Release [ID: 452]...")
    for test in test_case_ids:
        mapping_payload = [test]
        try:
            release_post = requests.post(
                f"{base_url}/projects/{project_id}/releases/452/test-cases", 
                json=mapping_payload, 
                headers=headers,
                timeout=30
            )
            if release_post.status_code in [200, 201, 202]:
                print(f"   📍 Mapped Case ID [{test}] to Release 452")
            else:
                print(f"   ❌ Release mapping failed for Case ID [{test}]: HTTP {release_post.status_code}")
        except Exception as e:
            print(f"   ❌ Network fault mapping case {test}: {e}")
        time.sleep(0.2)

print("\n🏁 Process complete!")