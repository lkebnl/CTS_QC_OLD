import logging
import os
import time
import subprocess
from datetime import datetime
import QC_components.qc_log as main_dict
import csv
import a_root_path as aroot

# common use the top_path
csv_data = {}
csv_file = 'femb_info.csv'
file_path = r'.\femb_info.csv'
root_path = aroot.root_path
root_python = aroot.root_python
with open(csv_file, mode='r', newline='', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) == 2:
            key, value = row
            csv_data[key.strip()] = value.strip()
main_dict.top_path = csv_data['top_path']
top_path = main_dict.top_path
print(top_path)
target_folder = root_path + 'Data/'
last_scan_file = root_path + 'Data/last_scan_results.txt'

def save_last_scan_results(results):
    with open(last_scan_file, 'w') as f:
        for file_path in results:
            f.write(file_path + '\n')

def load_last_scan_results():
    results = set()
    if os.path.exists(last_scan_file):
        with open(last_scan_file, 'r') as f:
            for line in f:
                results.add(line.strip())
    return results

def subrun(command, timeout=30, check=True, exitflg=True, user_input=None):
    global result
    try:
        result = subprocess.run(command,
                                input = user_input,
                                capture_output=True,
                                text=True,
                                timeout=timeout,
                                shell=True,
                                check=check
                                )
    except subprocess.CalledProcessError as e:
        print("Call Error", e.returncode)
        if exitflg:
            print("Call Error FAIL!")
            print("Exit anyway")
            return None
            # exit()
        # continue
    except subprocess.TimeoutExpired as e:
        print("No reponse in %d seconds" % (timeout))
        if exitflg:
            # print (result.stdout)
            print("Timoout FAIL!")
            print("Exit anyway")
            return None
            # exit()
        # continue
    return result



logs = {}

def real_time_monitor():
    previous_files = load_last_scan_results()
    while True:
        current_files = set()
        for root, dirs, files in os.walk(target_folder):
            for file in files:
                current_files.add(os.path.join(root, file))
        # calculate new update document
        new_files = current_files - previous_files
        # update the scan result
        previous_files = current_files

        save_last_scan_results(current_files)

        for file_path in new_files:
            n = []
            c = 0
            print(f'new file detected: {file_path}')
            if '_S0' in file_path:
                n.append(0)
                c+=1
            if '_S1' in file_path:
                n.append(1)
                c += 1
            if '_S2' in file_path:
                n.append(2)
                c += 1
            if '_S3' in file_path:
                n.append(3)
                c += 1

            desired_path = os.path.dirname(file_path)  # get last path
            path = os.path.dirname(desired_path)  # get last path
            path = path.replace('\\', '/')  # get last path
            t_char = file_path[-7:]
            t_num = ''.join([char for char in t_char if char.isdigit()])
            if '_t' in file_path[-9:]:
                if '_t6' in file_path[-9:]:
                    time.sleep(c*30)  # the time is used to copy the whole .bin file
                else:
                    time.sleep(c*7)  # the time is used to copy the whole .bin file
                command = [root_python, "QC_report_all.py", path, "-n"]
                command.extend(map(str, n))  # Convert integers to strings
                command.extend(["-t", t_num])  # Add other arguments
                print(command)
                result = subrun(command, timeout=1000)  # rewrite with Popen later
        time.sleep(5)   # when monitor works in wait, 5 seconds wait in one scan cycle

directory__Report_path = root_path + 'FEMB_QC/Report'
if not os.path.exists(directory__Report_path):
    os.makedirs(directory__Report_path)
    print(f"Directory '{directory__Report_path}' created.")
else:
    print(f"Directory '{directory__Report_path}' already exists. ")

directory_Data_path = root_path + 'FEMB_QC/Data'
if not os.path.exists(directory_Data_path):
    os.makedirs(directory_Data_path)
    print(f"Directory '{directory_Data_path}' created.")
else:
    print(f"Directory '{directory_Data_path}' already exists. ")


real_time_monitor()

if True:
    logging.basicConfig(filename='D:/FEMB_QC/Data/QC.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('info: %s', logs)
