import time
from wib_cfgs import WIB_CFGS
import sys
import pickle
import copy
import datetime
import components.assembly_parameter as paras
import components.assembly_log as log
import components.assembly_function as a_func
import components.assembly_report as a_repo
import components.assembly_CSV_report as a_CSV
import matplotlib.pyplot as plt


# ============================
t1 = time.time()
####### Input FEMB slots #######
if len(sys.argv) < 2:
    print('Please specify at least one FEMB # to test')
    print('e.g. python3 quick_checkout.py 0')
    exit()

if 'save' in sys.argv:
    save = True
    for i in range(len(sys.argv)):
        if sys.argv[i] == 'save':
            pos = i
            break
    sample_N = int(sys.argv[pos + 1])
    sys.argv.remove('save')
    fembs = [int(a) for a in sys.argv[1:pos]]
else:
    save = False
    sample_N = 1
    fembs = [int(a) for a in sys.argv[1:]]

if 'sp' in sys.argv:
    ship = True
else:
    ship = False

if 'LF' in sys.argv:
    Rail = False
else:
    Rail = True

if 'OW' in sys.argv:
    NewWIB = False
else:
    NewWIB = True

###########################################
#      PART 01 Input test information     #
###########################################

if save:
    logs = {}
    tester = input("please input your name:  ")
    logs['Operator'] = tester

    env_cs = input("Test is performed at cold(LN2) (Y/N)? : ")
    if ("Y" in env_cs) or ("y" in env_cs):
        env = "LN"
    else:
        env = "RT"
    logs['env'] = env

    ToyTPC_en = input("ToyTPC at FE inputs (Y/N) : ")
    if ("Y" in ToyTPC_en) or ("y" in ToyTPC_en):
        toytpc = "100pF"
    else:
        toytpc = "0pF"
    logs['Toy_TPC'] = toytpc

    note = input("A short note (<200 letters):")
    logs['Note'] = note

    fembName = {}
    fembNo = {}
    for i in fembs:
        fembName['femb{}'.format(i)] = input("FEMB{}ID:".format(i)).strip()
        fembNo['femb{}'.format(i)] = fembName['femb{}'.format(i)][1:]
    logs['FEMB ID'] = fembName
    # logs['femb id']=fembNo
    logs['date'] = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

    datadir = a_func.Create_data_folders(fembName, env, toytpc)
    fp = datadir + "logs_env.bin"
    with open(fp, 'wb') as fn:
        pickle.dump(logs, fn)

outfile = open(datadir + "chk_logs.txt", "w")
t1 = time.time()

log.report_log01["ITEM"] = "01 Initial Information"
log.report_log01["Detail"] = logs
# ======================================

chk = WIB_CFGS()
chk.wib_fw()

print("Power off FEMBs to initial")
chk.femb_powering([])
chk.fembs_vol_set(vfe = 3.0, vcd = 3.0, vadc = 3.5)

for ifemb in fembs:
    chk.femb_powering_single(ifemb, 'on')

# set switch on monitoring path
chk.wib_mon_switches(dac0_sel=0, dac1_sel=0, dac2_sel=0, dac3_sel=0, mon_vs_pulse_sel=0,inj_cal_pulse=0)
for femb_id in fembs:
    chk.femb_cd_gpio(femb_id=femb_id, cd1_0x26=0x03, cd1_0x27=0x1f, cd2_0x26=0x00, cd2_0x27=0x1f)