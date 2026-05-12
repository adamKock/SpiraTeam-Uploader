import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
load_dotenv()

api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key
headers["project-id"]=project_id

filepath = "dhwiuhiewbdew.csv"

df = pd.read_csv(filepath)


#Clean the DF 
#Get the test case folder details in a list of dicts 
#Create and submit the test case and step payloads
#After creating the test cases and steps move them into the folders


def clean_df(df):
    #What Data do we want to clean, blank full rows
    #Full Blank Cols 
    df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
    df.columns = df.columns.str.strip()
    return df 

