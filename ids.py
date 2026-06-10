import os
import requests
import json
from dotenv import load_dotenv

# --- Load Environment & Configuration ---
load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url = os.getenv("SPIRA_URL")

headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"] = username
headers["api-key"] = api_key

# --- Configuration ---
# The name of the custom property you are looking for.
# The ID of the specific incident you want to inspect.
INCIDENT_ID = 6687  # <--- Change this to the incident you want to check
CUSTOM_PROPERTY_NAME = "Root Cause"

print(f"🔍 Searching for '{CUSTOM_PROPERTY_NAME}' in Incident ID: {INCIDENT_ID}...")

try:
    # 1. Get the data for the specific incident
    incident_url = f"{base_url}/projects/{project_id}/incidents/{INCIDENT_ID}"
    response = requests.get(incident_url, headers=headers)
    response.raise_for_status()  # This will raise an error for bad status codes (4xx or 5xx)
    incident_data = response.json()

    # 2. Loop through its custom properties to find 'Root Cause'
    root_cause_id = None
    custom_properties = incident_data.get("CustomProperties", [])
    for prop in custom_properties:
        # Check if the property's definition name is 'Root Cause'
        if prop.get("Definition", {}).get("Name") == CUSTOM_PROPERTY_NAME:
            root_cause_id = prop.get("IntegerValue")
            break # Stop searching once we've found it

    # 3. Print the result
    if root_cause_id is not None:
        print(f"✅ Found! The '{CUSTOM_PROPERTY_NAME}' ID for this incident is: {root_cause_id}")
    else:
        print(f"❌ The '{CUSTOM_PROPERTY_NAME}' field was not found or is not set for this incident.")

except requests.exceptions.RequestException as e:
    print(f"\nAn API error occurred: {e}")
    if e.response:
        print(f"Response Body: {e.response.text}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
