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
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key

req_id = None 
req_name = None
req_description = None

#Please Update the file path of your new file to upload 
file_path = "TestFileRequirementUpload.csv"
#Export path of the export CSV
export_path = "RequirementOutput.csv"

req_type_id=49
df = pd.read_csv(file_path, skiprows=1)

def clean_df(df):
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

    return df

#Create payload function 
def create_payload(df):
    payloads=[]
    for index, row in df.iterrows():
        req_name = str(row["Requirement Name"]).strip()
        if not req_name or req_name.lower() == "nan":
            print(f"Skipping row at index {index}")
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
        
    return payloads
        
#Submit Payload 
def submit_payload(payloads):
    created_items=[]
    futures=[]
    number = len(payloads)
    with ThreadPoolExecutor(2) as executor:
        for x, payload in enumerate(payloads):
            future = executor.submit(requests.post,f"{base_url}/projects/{project_id}/requirements", headers=headers, json=payload)
            futures.append(future)

        for i, future in enumerate(futures):
            response = future.result()

            if response.status_code in [200,201,202]:
                r = response.json()
                created_items.append(r)
                print(f"{i+1}/{number} Loaded: ID {r.get('RequirementId')}")
            else:
                print(f"{i+1}/{number} Failed: {response.status_code} - {response.text}")
        
    return created_items
            
def generate_csv(created_items, export_path):
    results_df = pd.DataFrame(created_items)
    results_df.to_csv(export_path, index=False)

df = clean_df(df)
payloads = create_payload(df)
items = submit_payload(payloads)
generate_csv(items, export_path)





 