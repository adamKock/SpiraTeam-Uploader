import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
import time  


load_dotenv()

api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("ESB_PRJ")
author_id = os.getenv("AUTH_ID")
base_url = os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id
session = requests.Session()
session.headers.update(headers)



#WHat we need to do is import CSV 
#Loop through each of the rows 
#Concat a few of them together 
#Create the test case and steps 


#df = pd.read_csv("WM IS AccessRoles TestCases.csv")

df = pd.read_csv("INT073.csv")

case_id = None
for index, row in df.iterrows():
    #print(df.columns)

    id = str(row.get("Test Case ID",""))
    test_case_name = str(row.get("TestCase Name",""))
    #role = str(row.get("Role",""))
    module = str(row.get("Module",""))
    priority = str(row.get("Priority",""))
    scope = str(row.get("Scope",""))
    comments = str(row.get("Comment",""))
    pre_conditions = str(row.get("Pre-conditions",""))
    test_data =  str(row.get("Test Data",""))
    steps =  str(row.get("Test Steps",""))
    expected_result=  str(row.get("Expected Results",""))
    fields = str(row.get("Fields",""))

    #TC Name to concat id and name 
    #Then in description need to concat 
    #Role 
    #Module
    #Scope
    #Comments

    tc_full_name = id + test_case_name
    combined_description = f"""
    **Module:** {module} **Fields** {fields} **Scope:** {scope} **Comment** {comments}"""

    #32 = Low 
    #31 Medium 
    #30 High 
    #29 Critial 

    #Now we need to create a hashmap with those values and then do mapping so when we provide high etc it gets the right id 

    p_map ={
         "Low":32,
         "Medium":31,
         "High":30,
         "Critical":29
    }

    p = p_map.get(priority)
    
    

    test_case_payload = {
                "Name": tc_full_name,
                "Description": str(combined_description),
                "ProjectID": str(project_id),
                "TestCaseFolderID": 9937,
                "AuthorID": 290,
                "TestCaseStatusId": 5,
                "TestCaseStatusName": "Ready for Test",
                "TestCasePriorityId":p
            }

    try: 
        response = session.post(
                        f"{base_url}/projects/{project_id}/test-cases", 
                        json=test_case_payload, 
                        headers=headers,
                        timeout=30)
        time.sleep(.5)

        if response.status_code in[200, 2001,202]:
            case_id = response.json()["TestCaseId"]
            print(f"Test Case created {case_id}")

            test_step_payload = {
                            "TestCaseId": case_id,
                            "Description": steps,
                            "ExpectedResult":expected_result,
                            "SampleData": test_data,
                            "Precondition":pre_conditions
                        }
            try:
                 test_step_response = session.post(f"{base_url}/projects/{project_id}/test-cases/{case_id}/test-steps",
                                                                headers=headers, json=test_step_payload)
                 print("Step Added ")
                 time.sleep(.5)

            except:
                 print("Error in creating the step")
                 



             
    except requests.exceptions.ConnectionError:
            print("⚠️ Connection closed by remote host. Pausing 3 seconds to recover gateway thresholds...")
            time.sleep(3.0)

            continue







		
