import sys
import numpy as np
import pickle
from scipy.fft import fft, fftfreq
import time, datetime, random, statistics
import matplotlib.pyplot as plt
import copy
from mpl_toolkits.mplot3d import Axes3D
import struct
from a91_spymemory_decode import wib_dec
import numpy as np
from scipy.stats import norm

# parameter
femb = 0
sample_time = 2

fp = 'D:/FEMB_Debug_Mode/CTS_QC/tmp_data/Raw_SE_900mVBL_14_0mVfC_2_0us_0x10.bin'
fembs = [femb]
# fp = sys.argv[1]
# sfn = fp.split("/")  # default
if "/" in fp:
    sfn = fp.split("/")
elif "\\" in fp:
    sfn = fp.split("\\")

p = fp.find(sfn[-1])
fdir = fp[0:p]

with open(fp, 'rb') as fn:
    raw = pickle.load(fn)
print(fp[p + 31:-4])
dac = fp[p + 31:-4]
rawdata = raw[0]
pwr_meas = raw[1]
runi = 0


wibdata = wib_dec(rawdata, fembs, spy_num=sample_time)

mean = 0
datdi = [0, 1, 2, 3, 4]
fechndata = []
for i in range(sample_time):
    wibdatai = wibdata[i]
    datdi[i] = [wibdatai[0], wibdatai[1], wibdatai[2], wibdatai[3]][fembs[0]]
print(len(datdi))
if sample_time == 1:
    datd = datdi[0]
elif sample_time == 2:
    datd = np.concatenate((datdi[0], datdi[1]), axis=1)
elif sample_time == 3:
    datd = np.concatenate((datdi[0], datdi[1], datdi[2]), axis=1)
elif sample_time == 4:
    datd = np.concatenate((datdi[0], datdi[1], datdi[2], datdi[3]), axis=1)
else:
    datd = np.concatenate((datdi[0], datdi[1], datdi[2], datdi[3], datdi[4]), axis=1)
# datd = datdi[0]

ref_chn = 7
if 1:
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 14})
    rms = []
    mean = []
    std = []
    pkp = []
    chn = 0
    channels_data = [None] * 128
    for fe in [0]: #[0, 1, 2, 3, 4, 5, 6, 7]:  # range(8):[0, 6]:#
        for fe_chn in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:  # range(16):[9]:#
            fechndata = np.array(datd[fe * 16 + fe_chn], dtype=np.int32)
            rms.append(np.mean(fechndata))
            rms_tmp = round(np.std(fechndata), 2)
            maxpos = np.argmax(fechndata[100:]) + 100
            maxvalue = fechndata[maxpos]
            baseline = np.mean(fechndata[maxpos-50: maxpos - 30])
            subaseline = [x - baseline for x in fechndata]
            #
            ch_mean = np.mean(fechndata)
            ch_std = np.std(fechndata)
            mean.append(ch_mean)
            std.append(ch_std)
            if np.mean(fechndata) > 2000:
                print('chip: {}, channel: {}, mean = {}, std = {}'.format(fe, fe_chn, ch_mean, ch_std))
            plt.plot(range(len(fechndata)), fechndata, label = '{}'.format(fe_chn))
            channels_data[chn] = fechndata
            chn += 1
    # labels = kmeans.predict(data_scaled)
    # print(kmeans.cluster_centers_)
    stdd = np.std(mean)
    yerr = stdd
    # plt.scatter(data[:, 0], data[:, 1],  cmap = 'viridis', s =50)
    m = np.mean(std)
    s = np.std(std)

print('channel_number = {}'.format(channels_data))
# mapping
print('\n')
print('- Back Up For Debug -------------------------------------------')
print('mapping to FEMB                          chip channel: ._[15:0]')
print('front:  chip_1_U07   chip_0_u03        chip_4_u19    chip_5_u21')
print('bottom: chip_3_U17   chip_2_u11        chip_6_u23    chip_7_u25')
print('---------------------------------------------------------------')
plt.grid()
plt.title(fp)
plt.legend()
# plt.tight_layout( rect=[0.05, 0.05, 0.95, 0.95])
plt.show()
plt.close()



exit()
