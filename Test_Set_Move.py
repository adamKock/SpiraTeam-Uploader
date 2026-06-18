import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json

print("=== 🚀 Starting Scenario Pattern-Based Spira Uploader ===")

# --- Load Environment Variables ---
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
author_id = os.getenv("AUTH_ID")
base_url = os.getenv("SPIRA_URL")
ms_user = os.getenv("MS")
client_user = os.getenv("PAYROLL")


headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"




#Get all the users and then put them into a dictionairy 
all_users = requests.get(f"{base_url}/projects/{project_id}/users", headers=headers).json()
user_map = {u["FullName"].strip().lower(): u["UserId"] for u in all_users}


#get all the test cases in the UAT release
all_tc = requests.get(f"{base_url}/projects/{project_id}/test-cases?starting_row=1&number_of_rows=99999&sort_field=&sort_direction=ASC&release_id=452", headers=headers).json()

#Get all the test sets apart of the release
all_test_sets = requests.get(f"{base_url}/projects/{project_id}/test-sets?starting_row=1&number_of_rows=99999&sort_field=&sort_direction=ASC&release_id=452", headers=headers).json()

# test_set_lookup will store: { "owner name": set_id }
test_set_lookup = {}

# mapped_cases_by_owner will store: { "owner name": set([TestCaseId1, TestCaseId2]) }
mapped_cases_by_owner = {}


#Loop through all the test sets that are in the release
for ts in all_test_sets:
    owner_key = ts["Name"].strip().lower()
    set_id = ts["TestSetId"]


    test_set_lookup[owner_key] = set_id

    # Fetch what is already inside this test set ONCE right now
    set_cases = requests.get(
        f"{base_url}/projects/{project_id}/test-sets/{set_id}/test-cases",
        headers=headers,
    ).json()
    mapped_cases_by_owner[owner_key] = {c["TestCaseId"] for c in set_cases}

#Loop through the test cases
for test in all_tc:
    #Assign some variables of the test case
    ownerid = test["OwnerId"]
    test_case_id = test["TestCaseId"]
    owner_name = test["OwnerName"]

    #if owner name val is blank skip test
    if not owner_name:
        continue
    
    owner_key = owner_name.strip().lower()

    #if owner name is not in the test_set_lookup dictionairy
    #Then go inside create a payload and then create the test set
    if owner_key not in test_set_lookup:
        print(f"➕ Creating new Test Set for: {owner_name}")
        payload = {
            "Name": owner_name,
            "TestSetStatusId": 1,
            "TestRunTypeId": 1,
            "OwnerId": ownerid,
            "ReleaseId": 452,  # Attach the test set to the release directly
        }

        create_res = requests.post(
            f"{base_url}/projects/{project_id}/test-sets",
            headers=headers,
            json=payload,
        )

        
        if create_res.status_code in [200, 201]:
            #Once we create we get the response and get the ID we then add that to the dict with the key being the owner name and the ID the test set ID we just created.
            new_set_id = create_res.json()["TestSetId"]
            test_set_lookup[owner_key] = new_set_id
            #Add it to the mapped test case by owner dictionairy 
            mapped_cases_by_owner[owner_key] = set()
        else:
            print(f"Error creating test set for {owner_key}")
            continue
    #Getting the target set id from the lookup dictionair 
    target_set_id = test_set_lookup[owner_key]

    #If the test case id is in the dictionairy of test case that has been mapped then skip
    if test_case_id in mapped_cases_by_owner[owner_key]:
        print(
            f"Skipping: Test Case {test_case_id} is already in {owner_key}'s Test Set."
        )
        continue

    print(f"Mapping Test Case {test_case_id} to {owner_key}'s Test Set...")
    

    # Use list of dictionairy comprehension to bulk make arrays and then hit the map end point
    mapping_payload = [{"TestSetId": target_set_id, "TestCaseId": test_case_id}]

    map_res = requests.post(f"{base_url}/projects/{project_id}/test-sets/{target_set_id}/test-case-mapping/{test_case_id}?owner_id={ownerid}&existing_test_set_test_case_id=",
        headers=headers,
        
    )

    if map_res.status_code in [200, 201, 202, 204]:
        # if the mapping works we update the test cases mapped dictionairy
        mapped_cases_by_owner[owner_key].add(test_case_id)
    else:
        print(f"⚠️ Mapping failed for Case {test_case_id}: {map_res.text}")

print("===Complete! Duplication removed and optimization applied. ===")

   