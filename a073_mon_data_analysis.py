import time
import sys
import numpy as np
import pickle
import copy
import os
import time, datetime, random, statistics
from QC_tools import ana_tools
import QC_check
import matplotlib.pyplot as plt

fdata = "./tmp_data/"

chkflag={"RMS":[],"BL":[],"Pulse_SE":{},"Pulse_DIFF":{},"PWR":[],"MON_T":[],"MON_BGP":[],"MON_ADC":{}}
chkflag["Pulse_SE"]={"PPK":[],"NPK":[],"BL":[]}
chkflag["Pulse_DIFF"]={"PPK":[],"NPK":[],"BL":[]}
chkflag["MON_ADC"]={"VCMI":[],"VCMO":[],"VREFP":[],"VREFN":[],"VSSA":[]}

badlist={"RMS":[],"BL":[],"Pulse_SE":{},"Pulse_DIFF":{},"PWR":[],"MON_T":[],"MON_BGP":[],"MON_ADC":{}}
badlist["Pulse_SE"]={"PPK":[],"NPK":[],"BL":[]}
badlist["Pulse_DIFF"]={"PPK":[],"NPK":[],"BL":[]}
badlist["MON_ADC"]={"VCMI":[],"VCMO":[],"VREFP":[],"VREFN":[],"VSSA":[]}

fmon = fdata+"Mon_200mVBL_14_0mVfC.bin"
with open(fmon, 'rb') as fn:
    rawmon = pickle.load(fn)
fadc = 1 / (2 ** 14) * 2500
mon_refs = rawmon[0]
mon_temps = rawmon[1]
mon_adcs = rawmon[2]
fembs = rawmon[3]
print(fembs)
mon_list = []
mon_GND_list = []
for nfemb in fembs:

    for key, mon_data in mon_refs.items():

        chip_list = []
        sps = len(mon_data)
        for j in range(sps):
            a_mon = mon_data[j][nfemb]
            chip_list.append(a_mon)

        if sps > 1:
            chip_list = np.array(chip_list)
            mon_mean = np.mean(chip_list)
        else:
            mon_mean = chip_list[0]
        mon_list.append(mon_mean * fadc)


for nfemb in fembs:

    # print(mon_adcs.keys())

    for key, mon_data in mon_temps.items():
        print(key); input()
        print(mon_data)
        chip_list = []
        sps = len(mon_data)
        for j in range(sps):
            a_mon = mon_data[j][nfemb]
            chip_list.append(a_mon)
        if sps > 1:
            chip_list = np.array(chip_list)
            mon_mean = np.mean(chip_list)
        else:
            mon_mean = chip_list[0]
        mon_GND_list.append(mon_mean * fadc)

print(mon_list)
print(mon_GND_list)
result = [round(x - y, 2) for x, y in zip(mon_list, mon_GND_list)]
print(result)
# fpwr = fdata+"PWR_SE_200mVBL_14_0mVfC_2_0us_0x00.bin"
# with open(fpwr, 'rb') as fn:
#     rawpwr = pickle.load(fn)
#
# pwr_meas=rawpwr[0]
# #for ifemb in fembs:
# for ifemb in range(len(fembs)):
#     tmp=QC_check.CHKPWR(pwr_meas,fembs[ifemb])
#     chkflag["PWR"].append(tmp[0])
#     badlist["PWR"].append(tmp[1])

nchips=range(8)
makeplot=True

#for ifemb in fembs:
for ifemb in range(len(fembs)):
    tmp = QC_check.CHKFET(mon_temps,fembs[ifemb],nchips,'RT')
    chkflag["MON_T"].append(tmp[0])
    badlist["MON_T"].append(tmp[1])


    tmp = QC_check.CHKFEBGP(mon_refs,fembs[ifemb],nchips,'RT')
    chkflag["MON_BGP"].append(tmp[0])
    badlist["MON_BGP"].append(tmp[1])

    tmp = QC_check.CHKADC(mon_adcs,fembs[ifemb],nchips,"VCMI",900,950)
    chkflag["MON_ADC"]["VCMI"].append(tmp[0])
    badlist["MON_ADC"]["VCMI"].append(tmp[1])

    tmp = QC_check.CHKADC(mon_adcs,fembs[ifemb],nchips,"VCMO",1200,1250)
    chkflag["MON_ADC"]["VCMO"].append(tmp[0])
    badlist["MON_ADC"]["VCMO"].append(tmp[1])

    tmp = QC_check.CHKADC(mon_adcs,fembs[ifemb],nchips,"VREFP",1900,1950)
    chkflag["MON_ADC"]["VREFP"].append(tmp[0])
    badlist["MON_ADC"]["VREFP"].append(tmp[1])

    tmp = QC_check.CHKADC(mon_adcs,fembs[ifemb],nchips,"VREFN",460,510)
    chkflag["MON_ADC"]["VREFN"].append(tmp[0])
    badlist["MON_ADC"]["VREFN"].append(tmp[1])

    tmp = QC_check.CHKADC(mon_adcs,fembs[ifemb],nchips,"VSSA",0,70)
    chkflag["MON_ADC"]["VSSA"].append(tmp[0])
    badlist["MON_ADC"]["VSSA"].append(tmp[1])
