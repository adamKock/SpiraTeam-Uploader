
import random
import json
import time

folder_info=[{
    "Name":"SIT",
    "ID":34323
}]

folder_info.append({
    "Name":"Adam",
    "ID":44322
})
folder_info.append({
    "Name":"Adam",
    "ID":44322
})
folder_info.append({
    "Name":"SIT",
    "ID":44322
})
folder_info.append({
    "Name":"Adam",
    "ID":44322
})
parent_folder="SIT"

for folder in folder_info:
    if folder["Name"] == parent_folder:
        print(folder["ID"])

def id_generator():
    return random.randint(1, 500)  

def response(foldername):
    res = {
        "status_code": 200,
        "TestCaseFolderName": foldername,
        "TestCaseFolderId": id_generator()
    }
    return res



random_string = "HYUDNWDQW"



lwr = random_string.lower()

print(lwr)



job_store={}
job_id=id_generator()

job_store[job_id] = {
            "requirements": random_string,
            "test_cases_ready": False,
            "created_at": time.time()
        }


print(job_store)