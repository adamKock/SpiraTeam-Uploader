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
username = os.getenv("USERNAME")


req_id = 7224
file_path = "reqtotes.csv"
project_id = 107
base_url = "https://digitalprograms.spiraservice.net/services/v7_0/RestService.svc"
headers = {
    "username": username,
    "api-key": api_key,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

get = requests.get(f"{base_url}/projects/{project_id}/requirements/{req_id}/test-cases", headers=headers)
r = get.json()
js = json.dumps(r, indent=4)
print(js)
