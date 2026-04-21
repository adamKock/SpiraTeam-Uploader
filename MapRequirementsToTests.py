#The uses will take the csvs 
#then create a mapping csv that gets uploaded and creates a mapping

import pandas as pd
import requests 
import csv
import os 
from dotenv import load_dotenv
import json



load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")


#Populate the mapping csv with the IDs in first column inser the IDs of the requirements 
#In second column have Ids of the test cases
#If you want one req to have 10 test cases you need to map the requirement to each of the test cases 
file_path = "MappingUpload.csv"
project_id = 107
base_url = "https://digitalprograms.spiraservice.net/services/v7_0/RestService.svc"
v7_url="https://api.inflectra.com/spira/services/v7_0/RestService.svc/projects/{project_id}/requirements/test-cases"
headers = {
    "username": username,
    "api-key": api_key,
    "Accept": "application/json",
    "Content-Type": "application/json"
}


df = pd.read_csv(file_path)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)

print(df.head)

for index, row in df.iterrows():
    create_payload={
        "RequirementId":str(row["RequirementId"]),
        "TestCaseId":str(row["TestCaseId"])
    }
    response = requests.post(f"{base_url}/projects/{project_id}/requirements/test-cases", headers=headers, json=create_payload)
    

    r = response.json()
    print(r)
    js = json.dumps(r, indent=4)
    print(js)