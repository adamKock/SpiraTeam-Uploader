
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









