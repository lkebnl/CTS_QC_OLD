import pickle
from a91_spymemory_decode import wib_dec
import numpy as np


fp = 'D:/FEMB_Debug_Mode/CTS_QC/tmp_data/K06_debug_Raw_SE_200mVBL_14_0mVfC_2_0us_0x00.bin'
fembs = [0]
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

# ** introduction for the data structure ** #
# raw[a][b][c] a should be 0, b is range at sample_time, c have 4 cell = [rawdata, 0, spy_rec_ticks, 0x00]
# raw[0][b][0] = bufs_bytes = [bytearray(DAQ_SPY_SIZE) for coldata in range(4*2)]
# raw[0][b][0][d]; d have 8 buffer corresponding to 8 COLDATA buffer in 4 FEMB boards
# print(raw[0][0][0][0])


print('\n')

wibdata = wib_dec(rawdata, fembs, spy_num=5)

mean = 0
datdi = [0, 1, 2, 3, 4]
fechndata = []
for i in range(5):
    wibdatai = wibdata[i]
    datdi[i] = [wibdatai[0], wibdatai[1], wibdatai[2], wibdatai[3]][fembs[0]]
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
    for fe in [3]:  # range(8):[0, 6]:#
        # for fe_chn in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:  # range(16):[9]:#
        for fe_chn in [1, 7]:  # range(16):[9]:#
            fechndata = np.array(datd[fe * 16 + fe_chn], dtype=np.int32)
            rms.append(np.mean(fechndata))
            rms_tmp = round(np.std(fechndata), 2)
            maxpos = np.argmax(fechndata[100:]) + 100
            maxvalue = fechndata[maxpos]
            baseline = fechndata[maxpos - 30]
            subaseline = [x - baseline for x in fechndata]
            #
            ch_mean = np.mean(fechndata)
            ch_std = np.std(fechndata)
            mean.append(ch_mean)
            std.append(ch_std)
            if np.mean(fechndata) > 2000:
                print('chip: {}, channel: {}, mean = {}, std = {}'.format(fe, fe_chn, ch_mean, ch_std))
                print('channel number = {}'.format(fe * 16 + fe_chn))
            plt.plot(range(len(fechndata)), fechndata)
            channels_data[chn] = fechndata
            chn += 1
    # labels = kmeans.predict(data_scaled)
    # print(kmeans.cluster_centers_)
    stdd = np.std(mean)
    yerr = stdd
    # plt.scatter(data[:, 0], data[:, 1],  cmap = 'viridis', s =50)
    m = np.mean(std)
    s = np.std(std)



# Analysis Detail
print('Total_channels = 0 ~ {}'.format(len(channels_data)-1))











####################################
print('\n')
print('- Back Up For Debug -------------------------------------------')
print('mapping to FEMB                          chip channel: ._[15:0]')
print('front:  chip_1_U07   chip_0_u03        chip_4_u19    chip_5_u21')
print('bottom: chip_3_U17   chip_2_u11        chip_6_u23    chip_7_u25')
print('---------------------------------------------------------------')

print('\n')
print('Configuration:')
print('Test_Slot: {}'.format(raw[1][0][0]))
print('ColdADC_0 Configuration: {}'.format(raw[1][0][1][0]))
print('ColdADC_1 Configuration: {}'.format(raw[1][0][1][1]))
print('ColdADC_2 Configuration: {}'.format(raw[1][0][1][2]))
print('ColdADC_3 Configuration: {}'.format(raw[1][0][1][3]))
print('ColdADC_4 Configuration: {}'.format(raw[1][0][1][4]))
print('ColdADC_5 Configuration: {}'.format(raw[1][0][1][5]))
print('ColdADC_6 Configuration: {}'.format(raw[1][0][1][6]))
print('ColdADC_7 Configuration: {}'.format(raw[1][0][1][7]))

print('LArASIC_0 Configuration: {}'.format(raw[1][0][2][0]))
print('LArASIC_1 Configuration: {}'.format(raw[1][0][2][1]))
print('LArASIC_2 Configuration: {}'.format(raw[1][0][2][2]))
print('LArASIC_3 Configuration: {}'.format(raw[1][0][2][3]))
print('LArASIC_4 Configuration: {}'.format(raw[1][0][2][4]))
print('LArASIC_5 Configuration: {}'.format(raw[1][0][2][5]))
print('LArASIC_6 Configuration: {}'.format(raw[1][0][2][6]))
print('LArASIC_7 Configuration: {}'.format(raw[1][0][2][7]))
print('Pulse_en = {}'.format(raw[1][0][3]))

# mapping

plt.grid()
# plt.tight_layout( rect=[0.05, 0.05, 0.95, 0.95])
plt.show()
plt.close()

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

mu1 = [None] * 128
sigma1 = [None] * 128
for i in range(128):
    baseline_data = channels_data[i] #np.array([...])  # 所有通道的RMS值
    mu1[i], sigma1[i] = norm.fit(baseline_data)

print(mu1)
print(sigma1)

# 假設 mu 是你已有的 128 個數據點
# mu = np.random.normal(loc=100, scale=5, size=128)  # 示例：生成一組隨機數據

# 繪製直方圖
plt.figure(figsize=(8, 5))
plt.hist(mu1, bins=20, edgecolor='black')  # 可以根據需求調整 bins 數量
plt.xlabel('Value of mu')
plt.ylabel('Frequency')
plt.title('Histogram of mu (128 data points)')
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
plt.hist(sigma1, bins=20, edgecolor='black')  # 可以根據需求調整 bins 數量
plt.xlabel('Value of mu')
plt.ylabel('Frequency')
plt.title('Histogram of mu (128 data points)')
plt.grid(True)
plt.tight_layout()
plt.show()

np.savetxt("channels_data.txt", channels_data, fmt="%d")

























'''


#
fp = 'D:/FEMB_Debug_Mode/CTS_QC/tmp_data/Raw_SE_200mVBL_14_0mVfC_2_0us_0x00_NS_T.bin'
fembs = [0]
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

# ** introduction for the data structure ** #
# raw[a][b][c] a should be 0, b is range at sample_time, c have 4 cell = [rawdata, 0, spy_rec_ticks, 0x00]
# raw[0][b][0] = bufs_bytes = [bytearray(DAQ_SPY_SIZE) for coldata in range(4*2)]
# raw[0][b][0][d]; d have 8 buffer corresponding to 8 COLDATA buffer in 4 FEMB boards
# print(raw[0][0][0][0])


print('\n')

wibdata = wib_dec(rawdata, fembs, spy_num=5)

mean = 0
datdi = [0, 1, 2, 3, 4]
fechndata = []
for i in range(5):
    wibdatai = wibdata[i]
    datdi[i] = [wibdatai[0], wibdatai[1], wibdatai[2], wibdatai[3]][fembs[0]]
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
    for fe in [0, 1, 2, 3, 4, 5, 6, 7]:  # range(8):[0, 6]:#
        for fe_chn in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:  # range(16):[9]:#
            fechndata = np.array(datd[fe * 16 + fe_chn], dtype=np.int32)
            rms.append(np.mean(fechndata))
            rms_tmp = round(np.std(fechndata), 2)
            maxpos = np.argmax(fechndata[100:]) + 100
            maxvalue = fechndata[maxpos]
            baseline = fechndata[maxpos - 30]
            subaseline = [x - baseline for x in fechndata]
            #
            ch_mean = np.mean(fechndata)
            ch_std = np.std(fechndata)
            mean.append(ch_mean)
            std.append(ch_std)
            if np.mean(fechndata) > 2000:
                print('chip: {}, channel: {}, mean = {}, std = {}'.format(fe, fe_chn, ch_mean, ch_std))
            plt.plot(range(len(fechndata)), fechndata)
            channels_data[chn] = fechndata
            chn += 1
    # labels = kmeans.predict(data_scaled)
    # print(kmeans.cluster_centers_)
    stdd = np.std(mean)
    yerr = stdd
    # plt.scatter(data[:, 0], data[:, 1],  cmap = 'viridis', s =50)
    m = np.mean(std)
    s = np.std(std)



# Analysis Detail
print('channel_number = {}'.format(len(channels_data)))











####################################
print('\n')
print('- Back Up For Debug -------------------------------------------')
print('mapping to FEMB                          chip channel: ._[15:0]')
print('front:  chip_0_U07   chip_3_u03        chip_4_u19    chip_7_u21')
print('bottom: chip_1_U17   chip_2_u11        chip_5_u23    chip_6_u25')
print('---------------------------------------------------------------')

print('\n')
print('Configuration:')
print('Test_Slot: {}'.format(raw[1][0][0]))
print('ColdADC_0 Configuration: {}'.format(raw[1][0][1][0]))
print('ColdADC_1 Configuration: {}'.format(raw[1][0][1][1]))
print('ColdADC_2 Configuration: {}'.format(raw[1][0][1][2]))
print('ColdADC_3 Configuration: {}'.format(raw[1][0][1][3]))
print('ColdADC_4 Configuration: {}'.format(raw[1][0][1][4]))
print('ColdADC_5 Configuration: {}'.format(raw[1][0][1][5]))
print('ColdADC_6 Configuration: {}'.format(raw[1][0][1][6]))
print('ColdADC_7 Configuration: {}'.format(raw[1][0][1][7]))

print('LArASIC_0 Configuration: {}'.format(raw[1][0][2][0]))
print('LArASIC_1 Configuration: {}'.format(raw[1][0][2][1]))
print('LArASIC_2 Configuration: {}'.format(raw[1][0][2][2]))
print('LArASIC_3 Configuration: {}'.format(raw[1][0][2][3]))
print('LArASIC_4 Configuration: {}'.format(raw[1][0][2][4]))
print('LArASIC_5 Configuration: {}'.format(raw[1][0][2][5]))
print('LArASIC_6 Configuration: {}'.format(raw[1][0][2][6]))
print('LArASIC_7 Configuration: {}'.format(raw[1][0][2][7]))
print('Pulse_en = {}'.format(raw[1][0][3]))

# mapping

plt.grid()
# plt.tight_layout( rect=[0.05, 0.05, 0.95, 0.95])
plt.show()
plt.close()

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

mu = [None] * 128
sigma = [None] * 128
for i in range(128):
    baseline_data = channels_data[i] #np.array([...])  # 所有通道的RMS值
    mu[i], sigma[i] = norm.fit(baseline_data)

print(mu1)
print(mu)
print(sigma1)
print(sigma)
plt.figure(figsize=(8, 5))
plt.plot(range(128), mu1)
plt.plot(range(128), mu)
plt.show()
plt.close()
# 假設 mu 是你已有的 128 個數據點
# mu = np.random.normal(loc=100, scale=5, size=128)  # 示例：生成一組隨機數據

# 繪製直方圖
plt.figure(figsize=(8, 5))
plt.hist(mu, bins=20, edgecolor='black')  # 可以根據需求調整 bins 數量
plt.xlabel('Value of mu')
plt.ylabel('Frequency')
plt.title('Histogram of mu (128 data points)')
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
plt.hist(sigma, bins=20, edgecolor='black')  # 可以根據需求調整 bins 數量
plt.xlabel('Value of mu')
plt.ylabel('Frequency')
plt.title('Histogram of mu (128 data points)')
plt.grid(True)
plt.tight_layout()
plt.show()

np.savetxt("channels_data.txt", channels_data, fmt="%d")



exit()
'''