import os
import sys
import time
import a_cts_ssh as cts
from PIL import Image
import csv
from colorama import init, Fore, Style
import a_root_path as aroot

# Please Open Real_Time_Monitor.py and run first
# Then, Run this CTS_FEMB_QC_top.py
############################################################
#       01 Function Part                                   #
############################################################
init()
root_path = aroot.root_path
def QC_Process(QC_TST_EN=None, input_info=None):
    while True:
        QCresult = cts.cts_ssh_FEMB(root=root_path, QC_TST_EN=QC_TST_EN, input_info=input_info)
        if QCresult != None:
            QCstatus = QCresult[0]
            badchips = QCresult[1]
            break
        else:
            print("139-> terminate, 2->debugging")
            userinput = input("Please contatc tech coordinator")
            if len(userinput) > 0:
                if "139" in userinput:
                    QCstatus = "Terminate"
                    badchips = []
                    break
                elif "2" in userinput[0]:
                    print("debugging, ")
                    input("click any key to start FEMB QC again ...")
    return QCstatus, badchips  # badchips range from 0 to7


# Before the test, you should move ssh-key to WIB
def FEMB_QC(input_info):
    # B Power On Warm Interface Board
    print("\033[35m" + "B00 : Turn Power Supply on to Power On WIB" + "\033[0m")
    # input("Enter to next ...\n")
    print("\033[35m" + "B01 : wait to Enable Fiber Converter [30 second]" + "\033[0m")
    time.sleep(30)
    print("\033[35m" + "B02 : Begin to Ping Warm Interface Board" + "\033[0m")
    QC_Process(QC_TST_EN=77, input_info=input_info)  # initial wib
    # first run
    # ###############STEP1#################################
    skts = [0, 1, 2, 3, 4, 5, 6, 7]

    # C FEMB QC
    print("\033[35m" + "C1 : FEMB initial (takes < 30s)" + "\033[0m")

    # ======== Button 00 WIB initial =====================
    # input("\033[35m" + 'Enter to Begin!' + "\033[0m")
    QC_Process(QC_TST_EN=0, input_info=input_info)  # initial wib
    QC_Process(QC_TST_EN=1, input_info=input_info)  # initial FEMB I2C
    return 0


############################################################
#       02 Execute Part                                    #
############################################################

# Warm FEMB QC (Room Temperature)
# A Before Power On

csv_file = 'femb_info.csv'
file_path = r'.\femb_info.csv'
print(Fore.GREEN + "A_RT00 : Install FEMB boards, check the connection of Data and Power Cables" + Style.RESET_ALL)
input_name = input('Please input your name: ')
print('\n')
# Initial_Scaner = input("Initial Scaner. \n\tEnter Any Key to exit ...\n\tEnter 'H' to check help")
# if (Initial_Scaner == 'H') or (Initial_Scaner == 'h'):
#     image = Image.open('D:\GitHub\BNL_CE_WIB_SW_QC\BNL_CE_WIB_SW_QC\Help\Initial_Scaner.png')
#     print('Close the picture to continue')
#     image.show()
print(Fore.CYAN + 'Record QR Code [with scaner or keyboard]' + Style.RESET_ALL)
# femb_id_0 = input('Scan the QR ID and assemble the CE box in the Bottom slot (Slot #0)\t')
m = input('Enter to next\nEnter m to add more FEMB')
if m == 'm':
    femb_id_0 = input('Scan the QR ID and assemble the CE box in the top slot [Slot #0]\t')
    femb_id_1 = input('Scan the QR ID and assemble the CE box in the top slot [Slot #1]\t')
    femb_id_2 = input('Scan the QR ID and assemble the CE box in the top slot [Slot #2]\t')
    femb_id_3 = input('Scan the QR ID and assemble the CE box in the top slot [Slot #3]\t')
else:
    femb_id_0 = 'debug_1'
    femb_id_1 = ''
    femb_id_2 = ''
    femb_id_3 = ''
print('\n')
print(Fore.GREEN + 'Please Review the info and put CE box into CTS chamber' + Style.RESET_ALL)
csv_data = {}
with open(csv_file, mode='r', newline='', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) == 2:
            key, value = row
            csv_data[key.strip()] = value.strip()
if 'tester' not in csv_data:
    csv_data['tester'] = 'sgao'
else:
    csv_data['tester'] = input_name
if 'SLOT0' not in csv_data:
    csv_data['SLOT0'] = 'H01'
else:
    csv_data['SLOT0'] = femb_id_0
if 'SLOT1' not in csv_data:
    csv_data['SLOT1'] = 'H02'
else:
    csv_data['SLOT1'] = femb_id_1
if 'SLOT2' not in csv_data:
    csv_data['SLOT2'] = 'H03'
else:
    csv_data['SLOT2'] = femb_id_2
if 'SLOT3' not in csv_data:
    csv_data['SLOT3'] = 'H04'
else:
    csv_data['SLOT3'] = femb_id_3
if 'test_site' not in csv_data:
    csv_data['test_site'] = 'BNL'
if 'toy_TPC' not in csv_data:
    csv_data['toy_TPC'] = 'y'
if 'comment' not in csv_data:
    csv_data['comment'] = 'Debug FEMB QC LN'
if 'top_path' not in csv_data:
    csv_data['top_path'] = 'D:/'
with open(csv_file, mode="w", newline="", encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    for key, value in csv_data.items():
        writer.writerow([key, value])
inform = cts.read_csv_to_dict(csv_file, 'RT')
print('\n')
print(Fore.GREEN + 'If the info is not right, enter "m" to modify the info. Else, just enter to next. [Enter "e" to exit; Enter "n" to skip the Warm QC]' + Style.RESET_ALL)
info_check = 'pass'
if info_check == 'm':
    os.system(f'notepad {file_path}')
    inform = cts.read_csv_to_dict(csv_file, 'RT')  # Warm test in Room Temperature
    print(Fore.YELLOW + 'please run the CTS_Real_Time_Monitor.py again, if the top_path is updated' + Style.RESET_ALL)

print(Fore.GREEN + "\nPlease Power On the WIB [Enter 'e' to exit;\tEnter 'n' to skip the Warm QC]" + Style.RESET_ALL)
Next = 'y'
if Next == 'n':
    print('No Warm QC execute!')
elif Next == 'e':
    Next2 = input("\nEnter Any Key to exit ...\nEnter 'N' to continue the LN test \n")
    if Next2 != 'y':
        sys.exit()
else:
    FEMB_QC(input_info=inform)
print('\n\n')
print('Great, WIB has been Initial!')
print('\n\n')

