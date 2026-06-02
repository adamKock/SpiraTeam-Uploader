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

filepath = "AK Core 2.6 csv.csv"

df = pd.read_csv(filepath, skiprows=3)


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
        
        test_case_payload = {
            "Name": tc_name,
            "Description": str(row.get("Test Case Description", "")) if pd.notna(row.get("Test Case Description")) else "",
            "ProjectID": str(project_id),
            "TestCaseFolderID": folder_id,
            "AuthorID": int(author_id) if author_id else None,
            "OwnerID": tester_id
        }
        
        response = requests.post(f"{base_url}/projects/{project_id}/test-cases", json=test_case_payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            case_id = response.json()["TestCaseId"]
            print(f"Created Test Case ID: [{case_id}]")
            
    else:
        # If it's not a new test case, it's a continuation row. Log it so you know it's working contextually
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
print("🏁 Smart upload complete! Checked all 'nan' leak paths successfully.")

        
   
            
        
           





      
    #Then we need to create the test step and then attach it to the test case to do this we will need to see if there is data in row step1, step2,step3,step4
    #If there is then create 




    





