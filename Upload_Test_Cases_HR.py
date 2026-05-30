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

filepath = "Slice of test cases for HR.csv"

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
all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers)
res = all_folders.json()
folder_details =[]
for folder in res:
    details={
        "Name":folder["Name"],
        "ID":folder["TestCaseFolderId"],
        "Parent Folder ID":folder["ParentTestCaseFolderId"]
    
    }
    folder_details.append(details)

all_users = requests.get(f"{base_url}/projects/{project_id}/users", headers=headers)
user_res = all_users.json()
user_details =[]
for user in user_res:
    user={
        "FullName":user["FullName"],
        "ID":user["UserId"]
    }
    user_details.append(user)



#The iterate through the csv creating the tests into the right folders 

    

    #get the process group id details (ID)
for index, row in df.iterrows():
    process_group_id = None 
    actor_id = None
    process_group_name = str(row["Process Group"])
    actor_user = str(row["Actor / User"])
    tester_name = str(row["Tester"])
    tester_name_id=None

    for folder in folder_details:
        if folder["Name"] == process_group_name:
            process_group_id = folder["ID"]
            break
    
    for user in user_details:
        if user["FullName"] == tester_name:
            tester_name_id = user["ID"]
            tester_name = user["FullName"]
            break
    
   

    #Then Create the test case and put it inside the process group folder which should like to the process group folder
    test_case_payload ={
        "Name":str(row["Test Case Name"]),
        "Descriptiom":str(row["Test Case Description"]),
        "ProjectID":project_id,
        "TestCaseFolderID":process_group_id,
        "AuthorID":author_id,
        "OwnerID":tester_name_id

    }
    response = requests.post(f"{base_url}/projects/{project_id}/test-cases", json=test_case_payload, headers=headers)

    if response.status_code in[200, 201,202]:
        r = response.json()
        case_id=r["TestCaseId"]
        test_name=r["Name"]
        description=r["Description"]
        folder_move = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/move?test_case_folder_id={actor_id}", headers=headers)

        #Loop through colums Step1,2,3,4
        csv_step_columns=["Step 1","Step 2","Step 3","Step 4"]

        for i, step_col in enumerate(csv_step_columns):
            step_text = row.get(step_col)

            if step_col== "Step 1":
                if pd.isna(step_text) or str(step_text).strip() =="":
                    description = str(row["Test Case Description"])

                else:
                    description=str(step_text)
            else:
                # If the cell is NaN or just whitespace, skip this column entirely
                if pd.isna(step_text) or str(step_text).strip() == "":
                    continue 
                else:
                    description = str(step_text)

      


            
            

            test_step_payload = {
                "TestCaseId": case_id, 
                "Description": description,
                "ExpectedResult": str(row.get("Expected Result", "")),
                "Position": i + 1 # This ensures steps are in order
            }

            test_step_response = requests.post(
                f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps", 
                headers=headers, 
                json=test_step_payload)
                   



            
        
           





      
    #Then we need to create the test step and then attach it to the test case to do this we will need to see if there is data in row step1, step2,step3,step4
    #If there is then create 




    





