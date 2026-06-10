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


def generate_incident_charts(df, phase_name):
    """
    Generates a standard set of incident charts for a given DataFrame.
    
    Args:
        df (pd.DataFrame): The DataFrame containing incident data for a specific phase.
        phase_name (str): The name of the test phase (e.g., 'SIT', 'UAT') for titles.
    """
    if df.empty:
        print(f"\n--- No incident data found for {phase_name} phase. Skipping charts. ---")
        return

    print(f"\n--- Generating Charts for {phase_name} ---")
    sns.set_theme(style="whitegrid")

    #-----Incident Status by Pie-----#
    fig, ax = plt.subplots()
    status_counts = df['IncidentStatusName'].value_counts().sort_values(ascending=False)
    if not status_counts.empty:
        ax.pie(status_counts, autopct='%1.1f%%', startangle=90, labels=status_counts.index.astype(str).tolist())
        ax.set_title(f'{phase_name}: Incident Distribution by Status')
        plt.show()

    #-----Priority by Bar-----#
    priority = df['PriorityName'].value_counts().sort_values(ascending=False)
    if not priority.empty:
        fig, ax = plt.subplots()
        ax.bar(x=priority.index, height=priority.values.astype(int).tolist(), color='skyblue')
        ax.set_title(f'{phase_name}: Incident Priority Breakdown')
        plt.show()

    #---Table for Priority and Status---#
    matrix_priority = pd.crosstab(df['PriorityName'], df['IncidentStatusName'])
    if not matrix_priority.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.suptitle(f'{phase_name}: Incident Priority vs. Status')
        ax.axis('off')
        ax.table(
            cellText=matrix_priority.values.astype(int).tolist(),
            rowLabels=matrix_priority.index.astype(str).tolist(),
            colLabels=matrix_priority.columns.astype(str).tolist(),
            loc='center',
            cellLoc='center'
        )
        plt.tight_layout()
        plt.show()

    #---Table for Severity and Status---#
    matrix_severity = pd.crosstab(df['SeverityName'], df['IncidentStatusName'])
    if not matrix_severity.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.suptitle(f'{phase_name}: Incident Severity vs. Status')
        ax.axis('off')
        ax.table(
            cellText=matrix_severity.values.astype(int).tolist(),
            rowLabels=matrix_severity.index.astype(str).tolist(),
            colLabels=matrix_severity.columns.astype(str).tolist(),
            loc='center',
            cellLoc='center'
        )
        plt.tight_layout()
        plt.show()

    #---Table for Owner and Status---#
    matrix_owner = pd.crosstab(df['OwnerName'], df['IncidentStatusName'], dropna=False)
    if not matrix_owner.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.suptitle(f'{phase_name}: Incident Owner vs. Status')
        ax.axis('off')
        ax.table(
            cellText=matrix_owner.values.astype(int).tolist(),
            rowLabels=matrix_owner.index.astype(str).tolist(),
            colLabels=matrix_owner.columns.astype(str).tolist(),
            loc='center',
            cellLoc='center'
        )
        plt.tight_layout()
        plt.show()

    #---- Root Cause Pie----#
    root_cause = df['Root Cause'].value_counts().sort_values(ascending=False)
    if not root_cause.empty:
        fig, ax = plt.subplots()
        ax.pie(root_cause, autopct='%1.1f%%', startangle=90, labels=root_cause.index.astype(str).tolist())
        ax.set_title(f'{phase_name}: Root Cause Analysis')
        plt.show()


# --- OVERALL CHART: Defects Per Phase ---
# This chart remains to give a high-level overview before the breakdown.
phase = defect_df['Test Phase'].value_counts().sort_values(ascending=False)
fig, ax = plt.subplots()
ax.bar(x=phase.index, height=phase.values.astype(int).tolist(), color='skyblue')
ax.set_title('Defects Per Phase')
plt.show()

# --- Generate Charts for Each Phase ---
sit_df = defect_df[defect_df['Test Phase'] == 'SIT'].copy()
uat_df = defect_df[defect_df['Test Phase'] == 'UAT'].copy()

generate_incident_charts(sit_df, 'SIT')
generate_incident_charts(uat_df, 'UAT')
