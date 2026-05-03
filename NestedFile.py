
import pandas as pd
import requests 
import csv
import os 
from dotenv import load_dotenv


folder_info =[]


def create_payload(df):
    case_id = None
    test_name = None
    description = None
    folder_id = None
    created_items = []

    for index, row in df.iterrows():
        row_type = str(row['Row Type']).strip()
        if row_type =="FOLDER" and row["Parent Folder Name"] is None:
            folder_payload={
                "Name": str(row["Test Case Name"]),

            }
            folder_response = requests.post(f"{base_url}/projects/{project_id}/test-folders", headers=headers, json=folder_payload)

            if folder_response.status_code in [200,201,202]:
                r = folder_response.json()
                print(r)
                folder_info.append([{
                    "Name":r["TestCaseFolderName"],
                    "ID":r["TestCaseFolderId"]
                }])
        
        elif row["Row Type"]=="FOLDER" and row["Parent Folder Name"] is not None:
            folder_payload={
                "Name": str(row["Test Case Name"]),

            }
            folder_response = requests.post(f"{base_url}/projects/{project_id}/test-folders", headers=headers, json=folder_payload)

            if folder_response.status_code in [200,201,202]:
                r = folder_response.json()
                folder_id=r["TestCaseFolderId"]
                folder_name=r["TestCaseFolderName"]
                folder_info.append([{
                    "Name":folder_name,
                    "ID":folder_id
                }])


                for folder in folder_info:
                   if folder["Name"].strip() == str(row["Parent Folder Name"]).strip():
                    parent_folder_id=folder["ID"]
                    move_folder = requests.post(f"{base_url}/projects/{project_id}/test-folders/{folder_id}/move?test_case_folder_id={parent_folder_id}", headers=headers, json=folder_payload)

                    

        elif row["Row Type"] == "TestCase":
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