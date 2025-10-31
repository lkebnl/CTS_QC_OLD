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



LAr_Dalay = 3.5
t1 = time.time()



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
    sample_N = int(sys.argv[pos+1] )
    sys.argv.remove('save')
    fembs = [int(a) for a in sys.argv[1:pos]]
else:
    save = False
    sample_N = 1
    fembs = [int(a) for a in sys.argv[1:]]



chk = WIB_CFGS()
chk.wib_fw()
chk.fembs_vol_set(vfe = 3.0, vcd = 3.0, vadc = 3.5)

