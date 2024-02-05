import os
import fnmatch

def list_json_files(folder_path):
    json_files_undecrypted = []
    json_file_decrypted = []
    for root, dirs, files in os.walk(folder_path):
        #print(len(dirs))
        for file in fnmatch.filter(files, '*.json'):
            if file.endswith('_decrypted.json'):
                json_file_decrypted.append(os.path.join(root, file))
            else:
                json_files_undecrypted.append(os.path.join(root, file))
    return [set(json_files_undecrypted), set(json_file_decrypted)] 

folder_path = '/home/lamisplus/server/temp'

# List all JSON files in the folder and its subfolders
json_files = list_json_files(folder_path)

print(f'decryted_file_count : {len(json_files[1])}')
print(f'undecrypted_file_count : {len(json_files[0])}')


#find /home/lamisplus/server/temp -type d | wc -l