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

all_test_cases = requests.get(f"{base_url}/projects/{project_id}/test-cases?starting_row={1}&number_of_rows={999}&sort_field={"TestCaseId"}&sort_direction={"ASC"}&release_id={"null"}", headers=headers)
res = all_test_cases.json()
print(res)
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
ax.set_title('Test Case Execution Status By Owner Matrix', fontsize=12, fontweight='bold', pad=15)
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
