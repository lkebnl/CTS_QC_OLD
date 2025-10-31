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

# qc_tools = ana_tools()
# Create an array to store the merged image
LAr_Dalay = 3.5

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

###########################################
#      PART 02 Initial Power Measurement  #
###########################################
chk = WIB_CFGS()
chk.wib_fw()

####### Power off FEMBs #######
print("Power off FEMBs to initial the test")
chk.femb_powering([])

RP = 1
if RP == 1:
    chk.fembs_vol_set(vfe=3.0, vcd=3.0, vadc=3.5)

#   set FEMB voltages
# chk.fembs_vol_set(vfe = paras.voltage_FE, vcd = paras.voltage_COLDATA, vadc = paras.voltage_ColdADC)
chk.fembs_vol_set(vfe=3.0, vcd=3.0, vadc=3.5)  # this parameter can not be used in LN2
# chk.fembs_vol_set(vfe = 4, vcd = 4, vadc = 4)
print("Check FEMB currents")
fembs_remove = []

for ifemb in fembs:
    chk.femb_powering_single(ifemb, 'on')
time.sleep(0.5)

chk.femb_cd_rst()
cfg_paras_rec = []
for i in range(8):
    chk.adcs_paras[i][8]=1   # enable  auto
for femb_id in fembs:
    chk.femb_cfg(femb_id, False )

#####   2.1  initial current measure #####
log.report_log02["ITEM"] = "2.1 Initial Current Measurement"
pwr_meas1 = chk.get_sensors()
result = False
for ifemb in fembs:
    femb_id = "FEMB ID {}".format(fembNo['femb%d' % ifemb])
    bias_i  =   round(pwr_meas1['FEMB%d_BIAS_I'%ifemb],3)
    fe_i    =   round(pwr_meas1['FEMB%d_DC2DC0_I'%ifemb],3)
    cd_i    =   round(pwr_meas1['FEMB%d_DC2DC1_I'%ifemb],3)
    adc_i   =   round(pwr_meas1['FEMB%d_DC2DC2_I'%ifemb],3)

    hasERROR = False
    if abs(bias_i)>paras.bias_i_low:
        print("ERROR: FEMB{} BIAS current |{}|>0.05A".format(ifemb,bias_i))
        hasERROR = True

    # if fe_i > paras.fe_i_high or fe_i < paras.fe_i_low:
    if  fe_i < paras.fe_i_low:
        print("ERROR: FEMB{} LArASIC current {} out of range (0.3A,0.6A)".format(ifemb,fe_i))
        hasERROR = True

    if cd_i>paras.cd_i_high:#  or cd_i<paras.cd_i_low :
        print("ERROR: FEMB{} COLDATA current {} out of range (0.1A,0.3A)".format(ifemb,cd_i))
        hasERROR = True

    # if adc_i>paras.adc_i_high or adc_i<paras.adc_i_low:
    #     print("ERROR: FEMB{} ColdADC current {} out of range (1.2A,1.8A)".format(ifemb,adc_i))
    #     hasERROR = True

    if hasERROR:
        print("FEMB ID {} Faild current check, will skip this femb".format(fembNo['femb%d'%ifemb]))
        log.report_log02[femb_id]['Part 2 Power Error List'] = "FEMB ID {} faild current #1 check\n".format(fembNo['femb%d' % ifemb])
        # fembs.remove(ifemb)

        #== I need to know how to merge the different dictionary, like the log here merge the log in induced function
        fembs_remove.append(ifemb)
        fembNo.pop('femb%d' % ifemb)
        chk.femb_powering_single(ifemb, 'off')
        result = False
    else:
        print("FEMB ID {} Pass current check".format(fembNo['femb%d'%ifemb]))
        result = True
for ifemb in range(len(fembs)):
    femb_id = "FEMB ID {}".format(fembNo['femb%d' % fembs[ifemb]])
    initial_power = a_func.power_ana(fembs, ifemb, femb_id, pwr_meas1, env)
    pwr1 = dict(log.tmp_log)
    check1 = dict(log.check_log)
    log.report_log02.update(pwr1)
    log.report_log021.update(check1)



for femb_id in fembs_remove:
    fembs.remove(femb_id)

if len(fembs) == 0:
    print ("All FEMB fail, exit anyway")
    exit()

chk.femb_powering(fembs)    #   close the FEMB channel without link

##### 2.2 check the default COLDATA and COLDADC register ##################
#   report in log03
if True:
    print("Check FEMB registers")
    log.report_log03["ITEM"] = "2.2 Check FEMB Registers"
    #   reset 3-ASIC
    a_func.chip_reset(fembs)
    check1 = a_func.register_check(fembs, fembNo, 1)
    ################ reset COLDATA, COLDADC and LArASIC ##############
    a_func.chip_reset(fembs)
    ################ check the default COLDATA and COLDADC register ###########
    print("Check FEMB registers second times")
    check2 = a_func.register_check(fembs, fembNo, 2, True)

if len(fembs) == 0:
   print ("All FEMB fail, exit anyway")
   exit()

################# enable certain fembs ###################
chk.wib_femb_link_en(fembs)
############################################
#      PART 03 SE Performance Measurement  #
############################################
#   create report dir
datareport = a_func.Create_report_folders(fembs, fembName, env, toytpc, datadir)

##################################
#      PART 05 Monitor Path      #
##################################
###### Take monitoring data ######

snc = 0  # 900 mV
sg0 = 0;
sg1 = 0  # 14mV/fC
st0 = 1;
st1 = 1  # 2us3
#   initial configuration
chk.femb_cd_rst()
cfg_paras_rec = []
for i in range(8):
    chk.adcs_paras[i][8] = 1  # enable  auto

for femb_id in fembs:
    chk.set_fe_board(sts=1, snc=snc, sg0=sg0, sg1=sg1, st0=st0, st1=st1, swdac=1, dac=0x10)
    adac_pls_en = 1
    cfg_paras_rec.append((femb_id, copy.deepcopy(chk.adcs_paras), copy.deepcopy(chk.regs_int8), adac_pls_en))
    chk.femb_cfg(femb_id, adac_pls_en)  # enable the Pulse

def monitoring_path(fembs, snc, sg0, sg1, datadir, save, sps):
    sps = sps
    print("monitor bandgap reference")
    nchips = range(8)
    mon_refs = {}
    for i in nchips:  # 8 chips per femb
        adcrst = chk.wib_fe_mon(femb_ids=fembs, mon_type=2, mon_chip=i, snc=snc, sg0=sg0, sg1=sg1, sps=sps)
        mon_refs[f"chip{i}"] = adcrst[7]

    print("monitor temperature")
    mon_temps = {}
    for i in nchips:
        adcrst = chk.wib_fe_mon(femb_ids=fembs, mon_type=1, mon_chip=i, snc=snc, sg0=sg0, sg1=sg1, sps=sps)
        mon_temps[f"chip{i}"] = adcrst[7]

    print("monitor ColdADCs")
    mon_adcs = {}
    for i in nchips:
        time.sleep(0.001)
        mon_adc = chk.wib_adc_mon_chip(femb_ids=fembs, mon_chip=i, sps=sps)
        mon_adcs[f"chip{i}"] = mon_adc

    if save:
        fp = datadir + "Mon_{}_{}.bin".format("200mVBL", "14_0mVfC")

        with open(fp, 'wb') as fn:
            pickle.dump([mon_refs, mon_temps, mon_adcs, fembs], fn)

    return mon_refs, mon_temps, mon_adcs

mon_refs, mon_temps, mon_adcs = monitoring_path(fembs, snc, sg0, sg1, datadir, save, 10)
# a_func.mon_path_ana(fembs, mon_refs, mon_temps, mon_adcs, datareport, fembNo, env, NewWIB)

# ================   Final Report    ===================================
a_repo.final_report(datareport, fembs, fembNo, Rail)
a_CSV.final_CSV(datareport, fembs, fembNo, Rail)
t2 = time.time()
print('Time Consumption: {} s'.format(round(t2 - t1, 2)))

####### Power off FEMBs #######
print("Turning off FEMBs")
chk.femb_powering([])
print("\n\n\n\n\n\n")