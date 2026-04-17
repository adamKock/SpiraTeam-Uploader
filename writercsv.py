import json
import csv

employees = [["TestCaseID", "Name"],
             ["1234", "TC-01"], 
             ["55544", "TC-02"], 
             ["3232", "TC-03"]] 


file_path = "C:/Users/adam.knockelbergh/Documents/Spirauploader/output.csv" 

try:
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        for row in employees:
            writer.writerow(row)
        print(f"csv file '{file_path}'")
except FileExistsError:
    print("file in use")

