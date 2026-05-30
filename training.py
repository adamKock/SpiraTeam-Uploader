


new_dict={}


details={
    "Name":"Folder 111",
        "ID":123,
        "Parent Folder ID":203902
    }

new_dict.update(details)

print(new_dict)


detail={
    "Name":"Folder 113",
        "ID":123,
        "Parent Folder ID":23323
    }

new_dict.update(detail)

folder_name = new_dict.get("Name")
print(folder_name)

