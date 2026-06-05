import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
author_id = os.getenv("AUTH_ID")
base_url = os.getenv("SPIRA_URL")

headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key
headers["project-id"] = project_id
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"



get_all_release_tc = requests.get(f"{base_url}/projects/{project_id}/releases/452/test-cases", headers=headers).json()

release_ids={
    tc["TestCaseId"]
    for tc in get_all_release_tc
}

all_test_sets = requests.get(f"{base_url}/projects/{project_id}/test-sets?starting_row=1&number_of_rows=99999&sort_field=&sort_direction=ASC&release_id=452", headers=headers).json()

test_case_ids_in_sets = set()

for test_set in all_test_sets:
    test_set_id = test_set["TestSetId"]

    test_cases = requests.get(
        f"{base_url}/projects/{project_id}/test-sets/{test_set_id}/test-cases",
        headers=headers
    ).json()

    test_case_ids_in_sets.update(
        tc["TestCaseId"]
        for tc in test_cases
    )

missing_ids = release_ids - test_case_ids_in_sets

print(f"Missing {len(missing_ids)} test cases")

for tc_id in sorted(missing_ids):
    print(tc_id)




#WHat we need to do is loop through all the test sets and then perform a lookup to see if it's in the release