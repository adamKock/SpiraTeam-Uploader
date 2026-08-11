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
release_id=os.getenv("UAT_RELEASE")

all_test_cases = requests.get(f"{base_url}/projects/{project_id}/test-cases?starting_row={1}&number_of_rows={1500}&sort_field={"TestCaseId"}&sort_direction={"ASC"}&release_id={release_id}", headers=headers)
res = all_test_cases.json()
test_df = pd.DataFrame(res)

# VISUALIZATION 1: Test Case Execution Status Distribution (Clean Legend Fix)
# =========================================================================
fig, ax = plt.subplots(figsize=(7, 4))
status_counts = test_df['ExecutionStatusName'].value_counts().sort_values(ascending=False)
total_tests = status_counts.sum()

# 1. Generate clean text strings combining Name + Percent + Count for the legend
legend_labels = []
for status, count in status_counts.items():
    percentage = (count / total_tests) * 100
    legend_labels.append(f"{status}: {count} ({percentage:.1f}%)")

# 2. Draw the pie chart WITHOUT text inside the slices (removes all overlapping strings)
ax.pie(
    status_counts.values.astype(int).tolist(),  
    labels=None, 
    autopct=None, # 🌟 Removes the overlapping inner numbers entirely
    startangle=90, 
    colors=['#4CAF50', '#FF9800', '#F44336', '#9E9E9E'][:len(status_counts)]
)

# 3. Add the legend containing all text, counts, and percentages safely on the side
ax.legend(
    labels=legend_labels, 
    title="Status Breakdown", 
    loc="center left", 
    bbox_to_anchor=(1, 0.5)
)

ax.set_title('Test Case Execution Metrics Summary', fontsize=11, fontweight='bold', pad=10)

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
                    "Manage System Lists", "Managing Attendance", "Policies", "Security", "Onboarding", "Payroll", "Manage Performance", "Recruitment", "Reporting", "Finance Reports",
                      "Succession", "Worksuite", "Payroll Deductions","Payroll Earnings"]

folders_to_keep = {name: folder_map[name.lower()] for name in folders_names_to_keep if name.lower() in folder_map}

#Need to get the ids from the folders to keep, iterate through them 
#Call the end point get the test cases and we seperate out the folder name it came from 
#The status and then build a dataframe with all the test cases and the folders they came from to use as the reference for graphs 

all_test_cases_from_folders = []

import time

for fold in folders_to_keep:
    folder_id = folders_to_keep[fold]
    
    # Use a dictionary for query parameters for better readability and to avoid f-string issues.
    params = {
        "starting_row": 1,
        "number_of_rows": 50,
        "sort_field": "ExecutionStatus",
        "sort_direction": "ASC",
        "release_id": 452
    }
    
    print(f"Attempting to fetch folder {fold}... (Waiting up to 90 seconds)")
    
    # =====================================================================
    # PAGINATION LOOP FOR FETCHING ALL TEST CASES IN FOLDER
    # =====================================================================
    all_test_cases = []
    starting_row = 1
    number_rows = 50
    
    try:
        while True:
            # Update pagination keys for Spira's API
            params["starting_row"] = starting_row
            params["number_of_rows"] = number_rows
            
            print(f"Fetching rows {starting_row} to {starting_row + number_rows - 1} for folder {folder_id}...")
            
            # The new chunked API request
            response = requests.get(
                f"{base_url}/projects/{project_id}/test-folders/{folder_id}/test-cases", 
                headers=headers, 
                params=params,
                timeout=(15, 60)
            )
            
            if response.status_code == 200:
                chunk = response.json()
                
                if not chunk:
                    print("Finished fetching all pages.")
                    break
                    
                all_test_cases.extend(chunk)
                print(f"Successfully retrieved {len(chunk)} test cases.")
                starting_row += number_rows
                time.sleep(1)
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                break
                
    except requests.exceptions.Timeout as e:
        print(f"[TIMEOUT ERROR] Server took too long to reply for folder {folder_id}.")
        print("The network route may be blocked or this folder has too many test cases.")
        continue
    
    print(f"Total test cases successfully loaded for folder {folder_id}: {len(all_test_cases)}")
    
    if all_test_cases:
        test_case_df = pd.DataFrame(all_test_cases)
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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Optional
# =========================================================================
# 📊 LIVE PROCESSING FOR RUN TIME BURNDOWN CHART (FIXED DATES ALIGNMENT)
# =========================================================================

# 1. Establish absolute timeline bounds (Set these to match your actual UAT cycle)
start_date1 = pd.to_datetime('2026-06-18').date()
end_date1 = pd.to_datetime('2026-08-26').date()

# Create a clean date range array representing every day in your timeline
date_range = pd.date_range(start=start_date1, end=end_date1).date
total_days = len(date_range) - 1

# Total test cases loaded in scope
total_test_cases = len(test_cases) if not test_cases.empty else 100

# 🌟 FIX: Calculate Ideal Remaining Path mapped directly to your calendar date array length
ideal_remaining = [total_test_cases - (i * (total_test_cases / total_days)) for i in range(len(date_range))]

# 3. Calculate Live Actual Remaining Test Cases
actual_remaining: list[Optional[int]] = [total_test_cases] * len(date_range)

if not test_cases.empty and 'LastUpdateDate' in test_cases.columns:
    # Convert Spira dates to uniform Datetime stamps, ignoring timezone off-sets
    completed_dates = pd.to_datetime(test_cases['LastUpdateDate'], errors='coerce').dt.date
    
    # Filter for items matching our active execution criteria (e.g., passed, failed, blocked)
    is_executed = test_cases['ExecutionStatusName'].isin(['Passed', 'Failed', 'Blocked'])
    execution_days = completed_dates[is_executed].value_counts().sort_index()
    
    # Map completions precisely onto our sequential calendar days tracker
    cumulative_completed = 0
    current_date_today = pd.Timestamp.now().date() # Current baseline date reference: June 24, 2026
    
    for idx, current_day in enumerate(date_range):
        if idx == 0:
            continue
        
        # Pull completions recorded on this specific day
        day_completions = execution_days.get(date_range[idx], 0)
        cumulative_completed += day_completions
        
        # Don't plot data points for future dates that haven't occurred yet
        if date_range[idx] <= current_date_today:
            actual_remaining[idx] = max(0, total_test_cases - cumulative_completed)
        else:
            actual_remaining[idx] = None # Cuts line display cleanly at current date boundary

# =========================================================================
# 📊 DRAW THE LIVE BURNDOWN CHART
# =========================================================================
fig, ax = plt.subplots(figsize=(10, 5)) # Using 10 wide to give the 2-month span breathing room

# 🌟 FIX: Pass the raw date_range directly as the X axis variable instead of days_axis
ax.plot(date_range, ideal_remaining, label='Ideal Burndown Trend', color='#9E9E9E', linestyle='--', linewidth=2)

# Extract only valid data points up to today's date
valid_dates = [d for d, val in zip(date_range, actual_remaining) if val is not None]
valid_values = [val for val in actual_remaining if val is not None]

# 🌟 FIX: Plot actual progress cleanly against the identical date tracking points
ax.plot(valid_dates, valid_values, label='Actual Remaining Tests', color='#2196F3', marker='o', linewidth=2.5)

# Styling and Labels
ax.set_title('Live UAT Execution Burndown Tracking', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('UAT Plan Timeline Schedule', fontsize=10, labelpad=8)
ax.set_ylabel('Remaining Unexecuted Test Cases', fontsize=10, labelpad=8)

# 🌟 FIX: Format the X-axis using Matplotlib's native date formatting system
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

# Since your timeline spans over 60+ days, interval the ticks to every 7 days 
# so they stay clean, legible, and un-crowded!
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7)) 
fig.autofmt_xdate(rotation=30, ha='right')
# 🌟 FIX: Boundary limits must be raw date bounds instead of numeric index limits
ax.set_xlim(start_date1, end_date1)
ax.set_ylim(0, total_test_cases + (total_test_cases * 0.05 if total_test_cases > 0 else 5)) # Dynamic 5% top buffer padding
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right')

plt.tight_layout()
plt.show()
# =========================================================================
# 📊 SCOPED PROCESS-GROUP BURNDOWN (SPECIFIC FOLDERS ONLY - FIXED DATES)
# =========================================================================

# 🌟 STEP 1: Define exactly which folders you want to isolate for this chart
target_folders = ["IMT", "Service Desk", "Cyber", "Absence", "Change of Contract", 
                  "Employee Self Service", "Holiday","Manage Employees", "Manage Leavers", 
                  "Overtime","Position Management","Pay Inputs","Document Management", 
                  "Forms & Workflows", "Jobs & Job Assignments", "Letter Management", 
                  "Manage System Lists", "Managing Attendance","Organisation Structure",
                  "Policies", "Security", "System", "Payroll", "Reporting", "Finance Reports",
                  "Payroll Deductions","Payroll Earnings"]

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional

# =========================================================================
# 📊 1. CONFIGURATION & DATA PREPARATION
# =========================================================================

# Define target scope folders
target_fold = ["Payroll Deductions", "Payroll Earnings"]

# Filter the master dataframe down to target scope
# (Replaced 'test_cases' with your loaded DataFrame if already fetched)
if 'test_cases' in globals() and not test_cases.empty:
    scoped_df = test_cases[test_cases['Folder'].isin(target_fold)].copy()
else:
    # Safe fallback structure if running standalone
    scoped_df = pd.DataFrame()

# Establish UAT sprint window
start_date = pd.to_datetime('2026-06-18').date()
end_date = pd.to_datetime('2026-08-26').date()

# Create uniform sequential date array
date_range = pd.date_range(start=start_date, end=end_date).date
total_days = len(date_range) - 1

# Total scope baseline test cases (e.g., 218)
total_test_cases = len(scoped_df) if not scoped_df.empty else 218

# Calculate Ideal Remaining Vector (Linear descent to 0)
ideal_remaining = [
    total_test_cases - (i * (total_test_cases / total_days)) 
    for i in range(len(date_range))
]

# Initialize Live Actual Remaining Test Cases vector with None
actual_remaining: list[Optional[float]] = [None] * len(date_range)

# =========================================================================
# ⚙️ 2. CALCULATE LIVE ACTUAL REMAINING (STARTS AT 218)
# =========================================================================

if not scoped_df.empty and 'LastUpdateDate' in scoped_df.columns:
    # Standardize Spira timestamps into clean Python date objects
    scoped_df['CleanDate'] = pd.to_datetime(scoped_df['LastUpdateDate'], errors='coerce').dt.date
    
    # Identify executed test cases (Passed, Failed, Blocked)
    is_executed_mask = scoped_df['ExecutionStatusName'].isin(['Passed', 'Failed', 'Blocked'])
    executed_df = scoped_df[is_executed_mask]

    # 🌟 KEY FIX: Filter to ONLY include executions on or after the sprint start date
    sprint_executions = executed_df[executed_df['CleanDate'] >= start_date]
    execution_by_day = sprint_executions['CleanDate'].value_counts().sort_index()

    # 🌟 KEY FIX: Start cumulative completed at 0 so Day 1 opens at full 218 baseline
    cumulative_completed = 0
    current_date_today = pd.Timestamp.now().date()

    for idx, current_day in enumerate(date_range):
        # Accumulate tests completed on this specific calendar date
        day_completions = execution_by_day.get(current_day, 0)
        cumulative_completed += day_completions

        # Plot actual progress up to today's date; cut off line into the future
        if current_day <= current_date_today:
            actual_remaining[idx] = max(0, total_test_cases - cumulative_completed)
        else:
            actual_remaining[idx] = None

# =========================================================================
# 🎨 3. DRAW THE BURNDOWN CHART
# =========================================================================
fig, ax = plt.subplots(figsize=(10, 5))

# Plot Ideal Linear Trendline
ax.plot(
    date_range, 
    ideal_remaining, 
    label='Ideal Trendline', 
    color='#9E9E9E', 
    linestyle='--', 
    linewidth=2
)

# Extract non-future values up to today
valid_dates = [d for d, val in zip(date_range, actual_remaining) if val is not None]
valid_values = [val for val in actual_remaining if val is not None]

# Plot Actual Remaining Progress Line
folder_label = ", ".join(target_fold)[:25] + "..." if len(", ".join(target_fold)) > 25 else ", ".join(target_fold)
ax.plot(
    valid_dates, 
    valid_values, 
    label=f'Actual Remaining ({folder_label})', 
    color='#E91E63', 
    marker='o', 
    linewidth=2.5
)

# Dynamic Title Formatting
folder_title_string = ", ".join(target_fold)
if len(folder_title_string) > 40:
    folder_title_string = folder_title_string[:40] + "..."

ax.set_title(f'UAT Burndown Focus: {folder_title_string}', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Execution Timeline', fontsize=10, labelpad=8)
ax.set_ylabel('Remaining Unexecuted Test Cases', fontsize=10, labelpad=8)

# X-Axis Date Formatting (Intervaled every 7 days to avoid crowding)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
fig.autofmt_xdate(rotation=30, ha='right')

# Limits & Styling (using date2num to resolve Pylance/type-checker warnings)
ax.set_xlim(float(mdates.date2num(start_date)), float(mdates.date2num(end_date)))
ax.set_ylim(0, total_test_cases + (total_test_cases * 0.05 if total_test_cases > 0 else 5))
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right')

plt.tight_layout()
plt.show()

import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional

# =========================================================================
# 📡 1. FETCH ALL TEST CASES DIRECTLY BY RELEASE ID
# =========================================================================
release_id = 452
starting_row = 1
number_of_rows = 1500

url = (
    f"{base_url}/projects/{project_id}/test-cases"
    f"?starting_row={starting_row}"
    f"&number_of_rows={number_of_rows}"
    f"&sort_field=TestCaseId"
    f"&sort_direction=ASC"
    f"&release_id={release_id}"
)

print(f"📡 Fetching all test cases assigned to Release [{release_id}]...")
response = requests.get(url, headers=headers, timeout=60)

if response.status_code == 200:
    raw_tc_data = response.json()
    test_cases_df = pd.DataFrame(raw_tc_data)
    print(f"✅ Successfully loaded {len(test_cases_df)} test cases for Release {release_id}.")
else:
    print(f"❌ Failed to fetch test cases. HTTP Status: {response.status_code}")
    test_cases_df = pd.DataFrame()

# =========================================================================
# 📊 2. BUILD ACCURATE BURNDOWN CHART
# =========================================================================
start_date = pd.to_datetime('2026-06-18').date()
end_date = pd.to_datetime('2026-08-26').date()

date_range = pd.date_range(start=start_date, end=end_date).date
total_days = len(date_range) - 1

total_test_cases = len(test_cases_df) if not test_cases_df.empty else 1050

# Ideal vector
ideal_remaining = [
    total_test_cases - (i * (total_test_cases / total_days)) 
    for i in range(len(date_range))
]

actual_remaining: list[Optional[float]] = [None] * len(date_range)

if not test_cases_df.empty:
    # 🌟 FIX 1: Use 'ExecutionDate' first, fall back to 'LastUpdateDate' if missing
    if 'ExecutionDate' in test_cases_df.columns:
        test_cases_df['RawDate'] = test_cases_df['ExecutionDate'].fillna(test_cases_df.get('LastUpdateDate'))
    else:
        test_cases_df['RawDate'] = test_cases_df.get('LastUpdateDate')

    test_cases_df['CleanDate'] = pd.to_datetime(test_cases_df['RawDate'], errors='coerce').dt.date

    # Filter executed cases (Passed, Failed, Blocked)
    is_executed_mask = test_cases_df['ExecutionStatusName']=="Passed"

    #is_executed_mask = test_cases_df['ExecutionStatusName'].isin(['Passed', 'Failed', 'Blocked'])
    executed_df = test_cases_df[is_executed_mask]

    # Print debug info to console to verify execution count matches Spira
    print(f"📊 Debug Verification: Total Executed Cases Found = {len(executed_df)}")

    # 🌟 FIX 2: Group executions by date, treating pre-sprint or missing dates as Day 1 (Jun 18)
    pre_sprint_count = 0
    sprint_executions = {}

    for _, row in executed_df.iterrows():
        exec_date = row['CleanDate']
        # If executed before start_date or missing date, credit it to start_date
        if pd.isna(exec_date) or exec_date <= start_date:
            pre_sprint_count += 1
        else:
            sprint_executions[exec_date] = sprint_executions.get(exec_date, 0) + 1

    cumulative_completed = 0
    current_date_today = pd.Timestamp.now().date()

    for idx, current_day in enumerate(date_range):
        if current_day == start_date:
            # Include all pre-sprint / opening day completions on Day 1
            day_completions = pre_sprint_count
        else:
            day_completions = sprint_executions.get(current_day, 0)

        cumulative_completed += day_completions

        if current_day <= current_date_today:
            actual_remaining[idx] = max(0, total_test_cases - cumulative_completed)
        else:
            actual_remaining[idx] = None

# =========================================================================
# 🎨 3. DRAW THE CHART
# =========================================================================
fig, ax = plt.subplots(figsize=(10, 5))

# Plot Ideal Line
ax.plot(date_range, ideal_remaining, label='Ideal Trendline', color='#9E9E9E', linestyle='--', linewidth=2)

# Extract non-future values up to today
valid_dates = [d for d, val in zip(date_range, actual_remaining) if val is not None]
valid_values = [val for val in actual_remaining if val is not None]

# Plot Actual Progress
ax.plot(
    valid_dates, 
    valid_values, 
    label=f'Actual Remaining ({int(valid_values[-1]) if valid_values else total_test_cases} left)', 
    color='#2196F3', 
    marker='o', 
    linewidth=2.5
)

# Formatting
ax.set_title(f'UAT Release {release_id} Total Burndown ({total_test_cases} Test Cases)', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Execution Timeline', fontsize=10, labelpad=8)
ax.set_ylabel('Remaining Unexecuted Test Cases', fontsize=10, labelpad=8)

# Date formatting on X-axis (7-day intervals)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
fig.autofmt_xdate(rotation=30, ha='right')

# Axis limits
ax.set_xlim(float(mdates.date2num(start_date)), float(mdates.date2num(end_date)))
ax.set_ylim(0, total_test_cases + (total_test_cases * 0.05 if total_test_cases > 0 else 5))
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right')

plt.tight_layout()
plt.show()