import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv



load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
req_id = None 
req_name = None
req_description = None
created_items = []

file_path = "Nav.csv"
export_path = "reqtest_.csv"
project_id = 107
req_id = None
req_name = None
req_description = None
req_type_id=49
base_url = "https://digitalprograms.spiraservice.net/services/v6_0/RestService.svc"
headers = {
    "username": username,
    "api-key": api_key,
    "Accept": "application/json",
    "Content-Type": "application/json"
}


df = pd.read_csv("Navreq.csv", skiprows=1)
df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)
df = df.dropna(subset=['Requirement Name'])
df = df.replace('nan', '', regex=True)


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
print(df.head)

for index, row in df.iterrows():
    req_name = str(row["Requirement Name"]).strip()
    if not req_name or req_name.lower() == "nan":
        print(f"Skipping empty ghost row at index {index}")
        continue

    create_payload={
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
    }
    print(json.dumps(create_payload, indent=4))        # Pretty print JSON

    print(create_payload)

    response = requests.post(f"{base_url}/projects/{project_id}/requirements", headers=headers, json=create_payload)
    if response.status_code in [200,201,202]:
            r = response.json()
            print(r)
            req_id=r["RequirementId"]
            req_name=r["Name"]
            req_description=r["Description"]
            created_items.append({"RequirementId":req_id, "Name":req_name, "Description":req_description})
            print(f"Success we created{req_name}")

    r = response.json()
    print(r)
    js = json.dumps(r, indent=4)
    print(js)

if created_items :
  results_df = pd.DataFrame(created_items)
  results_df.to_csv(export_path, index=False)







