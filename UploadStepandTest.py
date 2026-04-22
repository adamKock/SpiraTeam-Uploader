import pandas as pd
import requests 
import csv
import os 
from dotenv import load_dotenv

#Script to link test cases to requirements 

#Run bulk import req function 
#As an output of each run store the IDs created and then generate a CSV with them
#Import bulk test case + steps script 
#As an output of each run store the IDs created and then generate a CSV with them
#Take the CSVs and then map the test cases to the req 
#Upload that csv to a custom script 


#Questions - Can we store the return values  and then convert to csv?
#Return values of Req are. ID, Name ?
#Return values of test case, ID, Name ?
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")


#Please Update the file path of your new file to upload 
file_path = "TestFileUpload.csv"
#Export path of the export CSV
export_path = "testcaseoutput.csv"
base_url = "https://digitalprograms.spiraservice.net/services/v7_0/RestService.svc"
headers = {
    "username": username,
    "api-key": api_key,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

endpoint="https://api.inflectra.com/spira/services/v7_0/RestService.svc/projects/{project_id}/test-cases"


df = pd.read_csv(file_path, skiprows=1)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)


case_id = None
test_name = None
description = None

created_items = []

for index, row in df.iterrows():
    row_type = str(row['Row Type']).strip()
    if row["Row Type"] == "TestCase":
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
            print(f"Success we created{test_name}")


    elif row["Row Type"]==">TestStep" and case_id is not None:
        test_step_payload ={
         "TestCaseId":case_id, 
         "Description":str(row["Test Step Description"]),
         "ExpectedResult":str(row["Expected Result"]),
         "Position":index,
         "SampleData":str(row["Sample Data"])
      }
        test_step_response = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps", headers=headers, json=test_step_payload)

#Creates output file as a CSV
if created_items :
  results_df = pd.DataFrame(created_items)
  results_df.to_csv(export_path, index=False)


