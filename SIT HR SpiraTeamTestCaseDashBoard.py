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
release_id=os.getenv("SIT_RELEASE")

all_test_cases = requests.get(f"{base_url}/projects/{project_id}/test-cases?starting_row={1}&number_of_rows={999}&sort_field={"TestCaseId"}&sort_direction={"ASC"}&release_id={release_id}", headers=headers)
res = all_test_cases.json()
test_df = pd.DataFrame(res)

# VISUALIZATION 1: Test Case Execution Status Distribution (Pie Chart)
# =========================================================================
fig, ax = plt.subplots(figsize=(6, 4))
status_counts = test_df['ExecutionStatusName'].value_counts().sort_values(ascending=False)

ax.pie(
    status_counts.values.astype(int).tolist(), 
    labels=status_counts.index.astype(str).tolist(), 
    autopct='%1.1f%%', 
    startangle=90, 
    colors=['#4CAF50', '#FF9800', '#F44336', '#9E9E9E'] # Standard Pass, Not Run, Fail, Blocked colors
)
ax.set_title('Test Case Execution Metrics Summary', fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
plt.show()

# =========================================================================
# VISUALIZATION 2: Test Case Assignment Status Matrix (Matplotlib Table)
# =========================================================================
# Generates a matrix tracking assignments against run outcomes
matrix = pd.crosstab(
    test_df['OwnerName'], 
    test_df['ExecutionStatusName'], 
    dropna=False
)

fig, ax = plt.subplots(figsize=(7, 4))

fig.suptitle('Test Case Execution Status By Owner Matrix', fontsize=12, fontweight='bold')
ax.axis('off')  # Strip plot axis grid lines from background

ax.table(
    cellText=matrix.values.astype(int).tolist(), 
    rowLabels=matrix.index.astype(str).tolist(), 
    colLabels=matrix.columns.astype(str).tolist(), 
    loc='center',
    cellLoc='center'
)
plt.tight_layout()
plt.show()

# =========================================================================
# VISUALIZATION 3: Test Case Management Workloads (Seaborn Bar Chart)
# =========================================================================
fig, ax = plt.subplots(figsize=(7, 4))
owner_counts = test_df['OwnerName'].value_counts().sort_values(ascending=False)

sns.barplot(
    x=owner_counts.index.astype(str).tolist(), 
    y=owner_counts.values, 
    ax=ax, 
    palette='magma'
)
ax.set_title('Assigned Workload Volumes per QA Tester', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Assigned Owner Account', fontsize=10)
ax.set_ylabel('Total Allocated Test Case Instances', fontsize=10)

plt.xticks(rotation=15) # Angle layout to ensure long tester profiles remain readable
plt.tight_layout()
plt.show()


# =========================================================================
# VISUALIZATION 4: Test Case Execution by Folders/Functional Area
# =========================================================================

#Iterate through that list to get all the test cases within them 

all_folders = requests.get(f"{base_url}/projects/{project_id}/test-folders", headers=headers).json()
folder_map = {f["Name"].strip().lower(): f["TestCaseFolderId"] for f in all_folders}

folders_names_to_keep =["IMT", "Service Desk", "Cyber", "Career Explorer", "Case Management", "Compensation", "Absence", "Change of Contract", 
                  "Employee Self Service", "Holiday", "Letter Management", "Manage Employees", "Manage Leavers", "Overtime", "Position Management",
                    "Pay Inputs", "System","Organisation Structure", "Document Management", "Forms & Workflows", "Jobs & Job Assignments", "Letter Management", 
                    "Manage System Lists", "Managing Attendance", "Policies", "Security", "Onboarding", "Payroll", "Performance", "Recruitment", "Reporting", "Finance Reports",
                      "Succession", "Worksuite", "Payroll Deductions","Payroll Earnings"]

folders_to_keep = {name: folder_map[name.lower()] for name in folders_names_to_keep if name.lower() in folder_map}

#Need to get the ids from the folders to keep, iterate through them 
#Call the end point get the test cases and we seperate out the folder name it came from 
#The status and then build a dataframe with all the test cases and the folders they came from to use as the reference for graphs 

all_test_cases_from_folders = []

for fold in folders_to_keep:
    folder_id = folders_to_keep[fold]
    
    # Use a dictionary for query parameters for better readability and to avoid f-string issues.
    params = {
        "starting_row": 1,
        "number_of_rows": 999,
        "sort_field": "ExecutionStatus",
        "sort_direction": "ASC",
        "release_id": 452
    }
    
    response = requests.get(f"{base_url}/projects/{project_id}/test-folders/{folder_id}/test-cases", headers=headers, params=params)
    
    if response.status_code == 200 and response.json():
        test_case_res = response.json()
        test_case_df = pd.DataFrame(test_case_res)
        test_case_df["Folder"] = fold
        all_test_cases_from_folders.append(test_case_df)

# Concatenate all DataFrames at once for better performance.
test_cases = pd.concat(all_test_cases_from_folders, ignore_index=True) if all_test_cases_from_folders else pd.DataFrame()
print(test_cases.columns)

    #Now we need to add the data from the res to a DF 
test_case_matrix = pd.crosstab(
test_cases['Folder'], 
test_cases['ExecutionStatusName'], 
dropna=False
)
# Add a 'Total' row at the bottom by summing each column
test_case_matrix.loc['Total'] = test_case_matrix.sum()

fig, ax = plt.subplots(figsize=(7, 4))
# Use fig.suptitle() to place the title at the top of the figure, not the axes.
fig.suptitle('Test Case Execution By Process Group', fontsize=12, fontweight='bold')
ax.axis('off')  # Strip plot axis grid lines from background

ax.table(
    cellText=test_case_matrix.values.astype(int).tolist(), 
    rowLabels=test_case_matrix.index.astype(str).tolist(), 
    colLabels=test_case_matrix.columns.astype(str).tolist(), 
    loc='center',
    cellLoc='center'
)
plt.tight_layout()
plt.show()