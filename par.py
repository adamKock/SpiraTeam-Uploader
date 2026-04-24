import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import time

load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")

req_id = None 
req_name = None
req_description = None
created_items = []



#Please Update the file path of your new file to upload 
file_path = "TestFileRequirementUpload.csv"
#Export path of the export CSV
export_path = "RequirementOutput.csv"
req_id = None
req_name = None
req_description = None
req_type_id=49
headers = {
    "username": username,
    "api-key": api_key,
    "Accept": "application/json",
    "Content-Type": "application/json"
}


df = pd.read_csv(file_path, skiprows=1)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)
df = df.dropna(subset=['Requirement Name'])
df = df.replace('nan', '', regex=True)

#This maps the MOSCOW in your CSV to Spira Moscow Spira IDs
spira_id_mapping = {
            "1 - high": 29,
            "2 - critical": 30,
            "3 - medium": 31,
            "4 - low": 32
        }

if "Importance" in df.columns:
    df["ImportanceId"] = df["Importance"].astype(str).str.lower().str.strip().map(spira_id_mapping).fillna(31).astype(int)
    df.drop("Importance", axis=1, inplace=True)


df.dropna(axis=0, how="all", inplace=True)

payloads = []

#Create payload function 

def create_payload(df):
    for index, row in df.iterrows():
        req_name = str(row["Requirement Name"]).strip()
        if not req_name or req_name.lower() == "nan":
            print(f"Skipping empty ghost row at index {index}")
            continue
        payloads.append({
        "Name":str(row["Requirement Name"]),
        "Description":str(row["Requirement Description"]),
        "ImportanceId":str(row["ImportanceId"]),
        "RequirementTypeId":req_type_id,
        "CustomProperties":[
            {
                "PropertyNumber" :1,
                "StringValue":str(row["Acceptance Criteria:"])

            }

        ]
    })
        

def submit_payload(payloads):
    with ThreadPoolExecutor(max_workers=3) as executor:
        for payload in payloads:
            future = executor.submit(requests.post, f"{base_url}/projects/{project_id}/requirements", headers=headers, json=payload)
            print(future.result())






