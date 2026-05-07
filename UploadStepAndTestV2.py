
import pandas as pd
import requests 
import os 
from dotenv import load_dotenv
import json


folder_info =[]
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key


def clean_df(df):
    df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
    df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)
    print(df.head)
    df.columns = df.columns.str.strip()
    #df.columns = df.columns.str.lower()
    


def create_payload(df):
    case_id = None
    test_name = None
    description = None
    folder_id = None
    folder_name = None
    created_items = []

    for index, row in df.iterrows():
        row_type = str(row['Row Type']).strip()
        if row_type.lower()=="folder":
            folder_payload={
                "Name": str(row["Test Case Name"]),

            }
            name = folder_payload.get("Name").lower() # type: ignore
            folder_response = requests.post(f"{base_url}/projects/{project_id}/test-folders", headers=headers, json=folder_payload)
            if folder_response.status_code in [200,201,202]:
                r = folder_response.json()
                folder_id=r["TestCaseFolderId"]
                folder_name=r["Name"]
                print(r)
                folder_info.append({
                    "Name":folder_name,
                    "ID":folder_id
                })
                
                if pd.notna(row["Parent Folder"]):
                    for folder in folder_info:
                        if folder["Name"].strip().lower() == str(row["Parent Folder"]).strip().lower():
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

        elif row_type == "TestCase":
            create_test_payload = {
                "Name": str(row["Test Case Name"]),
                "Description": str(row["Test Case Description"]),
                "ProjectID": project_id,
                "AuthorID":443
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

        elif row["Row Type"]==">TestStep" and case_id is not None:
            test_step_payload ={
            "TestCaseId":case_id, 
            "Description":str(row["Test Step Description"]),
            "ExpectedResult":str(row["Expected Result"]),
            "Position":index,
            "SampleData":str(row["Sample Data"])
        }
            test_step_response = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps", headers=headers, json=test_step_payload)

    return created_items



def generate_csv(created_items, export_path):
    results_df = pd.DataFrame(created_items)
    results_df.to_csv(export_path, index=False)

#Please Update the file path of your new file to upload 
file_path = "TestFileUpload.csv"
#Export path of the export CSV
export_path = "testcaseoutput.csv"

df = pd.read_csv(file_path, skiprows=1)
clean_df(df)
items = create_payload(df)
generate_csv(items, export_path)
