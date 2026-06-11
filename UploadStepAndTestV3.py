import pandas as pd
import requests 
import os 
from dotenv import load_dotenv
import json


load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key
author_id=os.getenv("AUTHOR_ID")


all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers)
res = all_folders.json()
folder_details =[]
for folder in res:
    details={
        "Name":folder["Name"],
        "ID":folder["TestCaseFolderId"],
        "Parent Folder ID":folder["ParentTestCaseFolderId"],
    
    }
    folder_details.append(details)
    

def clean_df(df):
    df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
    df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)
    df.columns = df.columns.str.strip()
    


def create_payload(df):
    case_id = None
    test_name = None
    description = None
    folder_id = None
    folder_name = None
    created_items = []
    parent_folder_id =None
    current_step_counter=1

    for index, row in df.iterrows():
        row_type = str(row['Row Type']).strip().lower()
        if row_type=="folder":
            #Now we need to loop to see if we have already created the folder 
            for folder in folder_details:
                if folder["Name"].strip().lower() == str(row["Test Case Name"]).strip().lower():
                    folder_id = folder["ID"]
                    folder_name = folder["Name"]
                    parent_folder_id = folder["Parent Folder ID"]
                    break
            else:
                folder_payload={
                    "Name": str(row["Test Case Name"]),
                }
                folder_response = requests.post(f"{base_url}/projects/{project_id}/test-folders", headers=headers, json=folder_payload)
                if folder_response.status_code in [200,201,202]:
                    r = folder_response.json()
                    folder_id=r["TestCaseFolderId"]
                    folder_name=r["Name"]
                    parent_folder_id=r["ParentTestCaseFolderId"]
                    print(r)
                    folder_details.append({
                        "Name":folder_name,
                        "ID":folder_id,
                        "Parent Folder ID":parent_folder_id

                    })
                    if pd.notna(row["Parent Folder"]):
                        for folder in folder_details:
                            if folder["Name"].strip().lower() == str(row["Parent Folder"]).strip().lower():
                                #Should also update the list of dict values with the parent folder ids too
                                parent_folder_id=folder["ID"]
                                parent_folder_name = folder["Name"]
                                print("Folder Moved to " + parent_folder_name + "Folder" )
                                folder_move_payload ={
                                    "TestCaseFolderId":folder_id,
                                    "ParentTestCaseFolderId":parent_folder_id,
                                    "Name":folder_name
                                }
                                move_folder = requests.put(f"{base_url}/projects/{project_id}/test-folders", headers=headers, json=folder_move_payload)
                        else:
                            continue
                else:
                    continue
        elif row_type == "testcase":
            current_step_counter=1
            create_test_payload = {
                "Name": str(row["Test Case Name"]),
                "Description": str(row["Test Case Description"]),
                "ProjectID": project_id,
                "AuthorID":author_id
                }
            response = requests.post(f"{base_url}/projects/{project_id}/test-cases", json=create_test_payload, headers=headers)

            if response.status_code in [200,201,202]:
                r = response.json()
                print(r)
                case_id=r["TestCaseId"]
                test_name=r["Name"]
                description=r["Description"]
                created_items.append({"TestCaseId":case_id, "Name":test_name, "Description":description})
            
                folder_move = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/move?test_case_folder_id={folder_id}", headers=headers)

            #Now if it is that then we need to create the test case and put it in the pre created folder 
        elif row_type==">teststep" and case_id is not None:
            test_step_index =1
            test_step_payload ={
            "TestCaseId":case_id, 
            "Description":str(row["Test Step Description"]),
            "ExpectedResult":str(row["Expected Result"]),
            "Position":index,
            "SampleData":str(row["Sample Data"])
        }
            test_step_response = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps", headers=headers, json=test_step_payload)
            if test_step_response.status_code in [200, 201, 202]:
            # INCREMENT COUNTER: Move to the next step sequence number
                current_step_counter += 1
         

            


    return created_items

def generate_csv(created_items, export_path):
    results_df = pd.DataFrame(created_items)
    results_df.to_csv(export_path, index=False)


export_path = "testcaseoutput.csv"
file_path = "TestFileUpload.csv"
df = pd.read_csv(file_path, skiprows=1)
clean_df(df)
items = create_payload(df)
generate_csv(items, export_path)