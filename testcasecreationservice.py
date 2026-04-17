import json 
import pandas as pd
import requests 

#We want to load the data
#Iterate through the rows 
#if the row is a test case then create the test case populate ID somewhere
#Else if the row is a step and case id is not none 
#create step payload that takes the case id, description and expected result and position (index from for loop)
#After creating payload create steps url from previous details 
#Hit endpoint 
import os 
api_key = os.getenv("API_KEY")
username = os.getenv("USERNAME")

file_path = "Nav.csv"
project_id = 107
base_url = "https://digitalprograms.spiraservice.net/services/v7_0/RestService.svc"
headers = {
    "username": "Adam.Kockelbergh@gatwickairport.com",
    "api-key": "{F939A427-0FF9-4D57-9475-4BD94A11F319}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

endpoint="https://api.inflectra.com/spira/services/v7_0/RestService.svc/projects/{project_id}/test-cases"

test_step_endpoint = "https://api.inflectra.com/spira/services/v7_0/RestService.svc/projects/{project_id}/test-cases/{test_case_id}/test-steps"

df = pd.read_csv(file_path,skiprows=1)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)


case_id = None

for index, row in df.iterrows():
   row_type = str(row['Row Type']).strip()
   if row["Row Type"] == "TestCase":
      test_case_payload = {
         "Name": str(row['Test Case Name']),
         "Description": str(row['Test Case Description']),
         "ProjectId": project_id,
         "TestCaseStatusId": 1,
         "AuthorID":316
      }
      test_case_response = requests.post(f"{base_url}/projects/{project_id}/test-cases", headers=headers, json=test_case_payload)
      if test_case_response.status_code in [200, 201]:
         r = test_case_response.json()
         case_id = r["TestCaseId"]

   elif row["Row Type"] ==">TestStep" and case_id is not None:
      test_step_payload ={
         "TestCaseId":case_id, 
         "Description":str(row["Test Step Description"]),
         "ExpectedResult":str(row["Expected Result"]),
         "Position":index,
         "Sample Data ":str(row["Sample Data"])
      }
      test_step_response = requests.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps", headers=headers, json=test_step_payload)
      if test_step_response.status_code in [200, 201]:
         r = test_step_response.json()




         


      

