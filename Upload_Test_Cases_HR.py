import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
load_dotenv()

api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
author_id = os.getenv("AUTH_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key
headers["project-id"]=project_id

filepath = "Coreforupload.csv"
test_case_ids =[]
spira_id_tracker = {}  # Maps CSV 'Ref' -> Spira 'TestCaseId'
pending_prereqs = []  # Tracks test cases requiring a post-upload description update


df = pd.read_csv(filepath)




#Clean the DF 
#Get the test case folder details in a list of dicts 
#Create and submit the test case and step payloads
#After creating the test cases and steps move them into the folders



#What Data do we want to clean, blank full rows
#Full Blank Cols 
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.dropna(axis=0,how="all", inplace=True)
df.columns.str.strip()

#Get All the folders in the project 

print("\nFetching folder cache and user maps from Spira...")
all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers).json()
folder_map = {f["Name"].strip().lower(): f["TestCaseFolderId"] for f in all_folders}

all_users = requests.get(f"{base_url}/projects/{project_id}/users", headers=headers).json()
user_map = {u["FullName"].strip().lower(): u["UserId"] for u in all_users}



#The iterate through the csv creating the tests into the right folders 

case_id = None
current_step_position = 1

    #get the process group id details (ID)
for index, row in df.iterrows():
    row_num = index
    # Grab the raw value
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
        tester_name = str(row.get("Tester ", "")).strip().lower()

        
        folder_id = folder_map.get(process_group_name)
        actor_id = folder_map.get(actor_user)
        tester_id = user_map.get(tester_name)
    
        raw_actor = row.get("Actor / User", "")

        actor_text = str(raw_actor).strip() if pd.notna(raw_actor) else ""
        base_description = (
            str(row.get("Test Case Description", ""))
            if pd.notna(row.get("Test Case Description"))
            else ""
        )

        # 3. Combine Actor and Description text together using Markdown formatting
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
            "OwnerName":tester_name,
            "TestCaseStatusId":5,
            "TestCaseStatusName":"Ready for Test"
        }
        
        response = requests.post(f"{base_url}/projects/{project_id}/test-cases", json=test_case_payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            case_id = response.json()["TestCaseId"]
            test_case_ids.append(case_id)
            print(f"Created Test Case ID: [{case_id}] with Owner {tester_name}")
            # Capture mapping between CSV Reference field and Spira ID
            csv_ref = str(row.get("Ref", "")).strip()
            if csv_ref and csv_ref.lower() != "nan":
                spira_id_tracker[csv_ref] = case_id

            # If row lists a prerequisite, cache it for Phase 2 processing
            prereq_val = str(row.get("Prerequisites", "")).strip()
            if prereq_val and prereq_val.lower() != "nan":
                pending_prereqs.append(
                    {
                        "target_spira_id": case_id,
                        "current_description": combined_description,
                        "prereq_csv_ref": prereq_val,
                    }
                )
        
           
    else:
        # If it's not a new test case, it's a continuation row. 
        if case_id is not None:
            print(f"   ↳ [Row {row_num}] Reading continuation steps for active Test Case ID [{case_id}]")

    
   

        #Loop through colums Step1,2,3,4
    csv_step_columns=["Step 1","Step 2","Step 3","Step 4"]

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
            
            print(f"Uploading Step -> Position [{current_step_position}]: '{step_description[:30]}...'")
            step_response = requests.post(
                f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps",
                headers=headers,
                json=step_payload
            )
            
            if step_response.status_code in [200, 201, 202]:
                    current_step_position += 1
            else:
                    print(f"     FAILED to write step. Status: {step_response.status_code}")

            print("\n" + "=" * 60)
print("🏁 Smart upload complete! Checked all 'nan' leak paths successfully. Time to map them to the release ")



if pending_prereqs:
    print("\n" + "=" * 60 + "\n⚡ Processing Prerequisite dependencies (Phase 2)...")
    for target in pending_prereqs:
        target_id = target["target_spira_id"]
        prereq_ref = target["prereq_csv_ref"]

        if prereq_ref in spira_id_tracker:
            prereq_spira_id = spira_id_tracker[prereq_ref]

            # Step A: GET the complete existing object to capture ConcurrencyDate and structure
            get_url = f"{base_url}/projects/{project_id}/test-cases/{target_id}"
            get_res = requests.get(get_url, headers=headers)
            
            if get_res.status_code == 200:
                tc_data = get_res.json()
                
                # Step B: Modify only the description field on the retrieved object
                prereq_text = f"\n\n**Prerequisite Test Case ID:** {prereq_spira_id}"
                tc_data["Description"] = f"{tc_data.get('Description', '')}{prereq_text}"

                # Step C: PUT the full object back to the plural test-cases route
                put_url = f"{base_url}/projects/{project_id}/test-cases"
                update_res = requests.put(put_url, json=tc_data, headers=headers)

                if update_res.status_code in [200, 204]:
                    print(f"Appended Prerequisite ID {prereq_spira_id} to Description of Spira ID {target_id}")
                else:
                    print(f"Failed to update Spira ID {target_id}: {update_res.text}")
            else:
                print(f"Could not fetch Spira ID {target_id} before update processing.")
        else:
            print(f"Prerequisite lookup failed for row referencing '{prereq_ref}'")



for test in test_case_ids:
        mapping_payload =[test]
        release_post = requests.post(f"{base_url}/projects/{project_id}/releases/452/test-cases", json=mapping_payload, headers=headers)

        if release_post.status_code in [200, 201, 202]:
            print("Test cases mapped to release")







      
    #Then we need to create the test step and then attach it to the test case to do this we will need to see if there is data in row step1, step2,step3,step4
    #If there is then create 




    





