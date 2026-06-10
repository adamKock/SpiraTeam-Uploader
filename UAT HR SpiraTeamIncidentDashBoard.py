import pandas as pd
import requests 
import os 
from dotenv import load_dotenv
import json
import matplotlib.pyplot as plt
import seaborn as sns


load_dotenv()
api_key = os.getenv("API_KEY")
username = os.getenv("SPIRA_USERNAME")
project_id = os.getenv("PROJECT_ID")
base_url=os.getenv("SPIRA_URL")
headers = json.loads(os.getenv("STD_HEADERS", "{}"))
headers["username"]=username
headers["api-key"]=api_key
author_id=os.getenv("AUTHOR_ID")


# 1. Define translation maps based on your Spira project's configuration values
root_cause_map = {
    4053: 'Code Defect',
    4054: 'Environment Issue',
    4058: 'Data Setup Configuration Error',
    # Add any extra IDs your team encounters here
}

test_phase_map = {
    4072: 'SIT',
    4073: 'UAT',
    # Add any extra IDs your team encounters here
}

all_incidents = requests.get(f"{base_url}/projects/{project_id}/incidents", headers=headers)
res = all_incidents.json()

parsed_incidents = []

for incident in res:
    item = {
        'IncidentId': incident.get('IncidentId'),
        'IncidentStatusName': incident.get('IncidentStatusName'),
        'PriorityName': incident.get('PriorityName'),
        'SeverityName': incident.get('SeverityName'),
        'Name': incident.get('Name'),
        'CreationDate': incident.get('CreationDate'),
        'ClosedDate': incident.get('ClosedDate'),
        'OwnerName': incident.get('OwnerName'),
        'Root Cause': 'Not Specified',
        'Test Phase': 'Not Specified'
    }
    
    custom_properties = incident.get('CustomProperties', [])
    for prop in custom_properties:
        definition_name = prop.get('Definition', {}).get('Name', '')
        assigned_id = prop.get('IntegerValue')
        
        # Safe type check conversion to resolve potential float conversion issues
        if assigned_id is not None:
            try:
                assigned_id = int(float(assigned_id))
            except (ValueError, TypeError):
                continue
                
            if definition_name == 'Root Cause':
                # Map the ID value. If it's a new ID not in our map, fall back to showing the raw ID string
                item['Root Cause'] = root_cause_map.get(assigned_id, f"ID: {assigned_id}")
                
            elif definition_name == 'Test Phase':
                item['Test Phase'] = test_phase_map.get(assigned_id, f"ID: {assigned_id}")
                
        elif definition_name == 'Test Phase' and prop.get('StringValue'):
            item['Test Phase'] = prop.get('StringValue')

    parsed_incidents.append(item)

defect_df = pd.DataFrame(parsed_incidents)


# Ensure styling looks professional
sns.set_theme(style="whitegrid")
# --- CHART 1: Incident Count by Status ---
# Sort values to guarantee the bars display in clean order
#-----Incident Status by Pie-----#
fig, ax = plt.subplots()
status_counts = defect_df['IncidentStatusName'].value_counts().sort_values(ascending=False)
ax.pie(status_counts,  autopct='%1.1f%%', startangle=90, labels=status_counts.index.astype(str).tolist())
ax.set_title('Incident Distribution by Status')
plt.show()


#-----Priority by Bar-----#
priority = defect_df['PriorityName'].value_counts().sort_values(ascending=False)
fig, ax = plt.subplots()
ax.bar(x=priority.index, height=priority.values.astype(int).tolist(), color='skyblue')
ax.set_title('Incident Priority Bar')
plt.show()


#---Table for Priority and Status
# 1. Get your basic summary counts
matrix = pd.crosstab(defect_df['PriorityName'], defect_df['IncidentStatusName'])
# 2. Open a blank plot sheet
fig, ax = plt.subplots()
ax.set_title('Incident Priority By Status')
ax.axis('off') # Hide the empty graph lines behind the table
# 3. Create the basic table
ax.table(
    cellText=matrix.values.astype(int).tolist(), 
    rowLabels=matrix.index.astype(str).tolist(), 
    colLabels=matrix.columns.astype(str).tolist(), 
    loc='center'
)
plt.show()

#---Table for Severity and Status
# 1. Get your basic summary counts
matrix = pd.crosstab(defect_df['SeverityName'], defect_df['IncidentStatusName'])

# 2. Open a blank plot sheet
fig, ax = plt.subplots()
ax.set_title('Incident Severity By Status')

ax.axis('off') # Hide the empty graph lines behind the table
# 3. Create the basic table
ax.table(
    cellText=matrix.values.astype(int).tolist(), 
    rowLabels=matrix.index.astype(str).tolist(), 
    colLabels=matrix.columns.astype(str).tolist(), 
    loc='center'
)
plt.show()


#---Table for Owner and Status
# 1. Get your basic summary counts
matrix = pd.crosstab(defect_df['OwnerName'], defect_df['IncidentStatusName'],dropna=False)

# 2. Open a blank plot sheet
fig, ax = plt.subplots()
ax.set_title('Incident Owner By Priority')

ax.axis('off') # Hide the empty graph lines behind the table
# 3. Create the basic table
ax.table(
    cellText=matrix.values.astype(int).tolist(), 
    rowLabels=matrix.index.astype(str).tolist(), 
    colLabels=matrix.columns.astype(str).tolist(),
    loc='center'
)
plt.show()

#---- Root Cause Pie----#
fig, ax = plt.subplots()
root_cause = defect_df['Root Cause'].value_counts().sort_values(ascending=False)
ax.pie(root_cause,  autopct='%1.1f%%', startangle=90, labels=root_cause.index.astype(str).tolist())
ax.set_title('Root Cause')
plt.show()

#-----Phase  Bar-----#
phase = defect_df['Test Phase'].value_counts().sort_values(ascending=False)
fig, ax = plt.subplots()
ax.bar(x=phase.index, height=phase.values.astype(int).tolist(), color='skyblue')
ax.set_title('Defects Per Phase')
plt.show()





