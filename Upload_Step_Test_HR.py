import pandas as pd
import requests 
import os 
from dotenv import load_dotenv
import json


folder_info =[]
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key
author_id=os.getenv("AUTHOR_ID")


#Clean data
#Get the folder information 
#Create and submit the test case payload 
#Create and submit the step payload and attach to the test case
#Move the test to the right folder


def clean_df(df):
    #Clean the rows 
    #Clean the cols
    df.drop(list(df.filter(regex='Unnamed:')), axis=1, inplace=True)
    df.drop(list(df.filter(regex='CUS-')), axis=1, inplace=True)
    print(df.head)
    df.columns = df.columns.str.strip()