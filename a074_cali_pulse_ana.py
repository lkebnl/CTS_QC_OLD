from spymemory_decode import wib_dec
import pickle
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import QC_components.qc_log as log
import QC_check as QC_check
import csv
from scipy import stats
import platform


def data_decode(raw, fembs):
    # wibdata = wib_dec(data=raw, fembs=fembs,fastchk = False, cd0cd1sync=True)
    wibdata = wib_dec(raw, fembs, spy_num=1, cd0cd1sync=False)
    return wibdata

def GetRMS(data, nfemb, fp, fname):
    """Calculate and plot the pedestal (PED) and root mean square (RMS) for each channel."""
    nevent = len(data)
    num_channels = 128
    ped, rms, pedmax, pedmin = [], [], [], []
    rms_max, rms_min = float('-inf'), float('inf')
    ped_max, ped_min = float('-inf'), float('inf')
    for ich in range(num_channels):
        allpls = np.concatenate([data[itr][nfemb][ich] for itr in range(nevent)])
        ch_ped = np.mean(allpls)
        ch_pedmax = np.max(allpls)
        ch_pedmin = np.min(allpls)
        ch_rms = np.std(allpls)
        ped.append(ch_ped)
        rms.append(ch_rms)
        pedmax.append(ch_pedmax)
        pedmin.append(ch_pedmin)
        rms_max = max(rms_max, ch_rms)
        rms_min = min(rms_min, ch_rms)
        ped_max = max(ped_max, ch_ped)
        ped_min = min(ped_min, ch_ped)
    fe_rms_med, fe_ped_med = np.median(rms), np.median(ped)
    return ped, rms, pedmax, pedmin






def GetPeaks(data, nfemb, fp, fname, funcfit=False, shapetime=2, period=500, dac = 0):
    global dat_tmts_l
    nevent = len(data)
    ppk_val = []
    npk_val = []
    bl_val = []
    ppk = []
    npk = []
    bl = []
    bl_rms = []
    # new=======
    dat_tmts_l = []
    dat_tmts_h = []
    for wibdata in data:
        dat_tmts_l.append(wibdata[nfemb][nfemb*2][0])
        dat_tmts_h.append(wibdata[nfemb][nfemb*2+1][0])
    dat_tmtsl_oft = (np.array(dat_tmts_l)//32)%period
    dat_tmtsh_oft = (np.array(dat_tmts_h)//32)%period
    all_data = []
    for achn in range(128):
        conchndata = []
        for i in range(len(data)):
            if achn < 64:
                oft = dat_tmtsl_oft[i]
            else:
                oft = dat_tmtsh_oft[i]
            wibdata = data[i]
            datd = [wibdata[0], wibdata[1], wibdata[2], wibdata[3]][nfemb]
            chndata = np.array(datd[achn], dtype = np.uint32)
            lench = len(chndata)
            tmp = int(period-oft)
            conchndata = conchndata + list(chndata[tmp : ((lench-tmp)//period)*period + tmp])
        all_data.append(conchndata)
    chns = list(range(128))
    rmss = []
    peds = []
    pkps, pkns = [], []
    pulse = []
    wfs, wfsf = [], []
    for achn in range(128):
        chdata = []
        N_period = len(all_data[achn])//period
        for iperiod in range(N_period):
            istart = iperiod*period
            iend = istart + period
            chunkdata = all_data[achn][istart : iend]
            chdata.append(chunkdata)
        chdata = np.array(chdata)
        avg_wf = np.average(np.transpose(chdata), axis = 1)
        wfsf.append(avg_wf)
        amax = np.max(avg_wf)
        amin = np.min(avg_wf)
        pkps.append(amax)
        pkns.append(amin)
        ppos = np.where(avg_wf == amax)[0][0]
        p0 = ppos + period
        peddata = []
        for iperid in range(N_period):
            if p0 < len(all_data[achn]):
                peddata += all_data[achn][p0 + iperid*period - 250: p0 + iperid*period - 50]
            else:
                if ppos > 250:
                    peddata += all_data[achn][ppos - 250: ppos - 50]
                else:
                    peddata += all_data[achn][ppos + 200: ppos + 400]
        rmss.append(np.std(peddata))
        peds.append(np.mean(peddata))
        pulse.append(np.round(avg_wf, 1))
        tmpwf =  avg_wf
        if ppos-50 < 0:
            front = avg_wf[-50 :]
            back = avg_wf[:-50]
            tmpwf = np.concatenate((front, back))
        ppos = np.where(tmpwf==np.max(tmpwf))[0][0]
        if ppos + 150 > period:
            front = tmpwf[ppos-50 : ]
            back = tmpwf[ : ppos - 50]
            tmpwf = np.concatenate((front, back))
        ppos = np.where(tmpwf == np.max(tmpwf))[0][0]
        wfs.append(tmpwf[ppos-50:ppos+150])
        if achn == 64:
            log.channel0_pulse[nfemb][dac] = tmpwf[ppos-50:ppos+150]# - np.mean(peddata)
    bottom = -1000
    fp_bin = fp + "Pulse_{}.bin".format(fname)
    # fp_bin = fp + "allPulse_{}.csv".format(fname)
    # with open(fp_bin, 'w') as fn:
    #     writer = csv.writer(fn)
    #     writer.writerows(pulse)
    return pkps, pkns, peds

def CheckLinearty(dac_list, pk_list, updac, lodac, chan, fp):
    #   first sample and fit
    #   the updac range need to be ensured
    dac_init = []
    pk_init = []
    for i in range(len(dac_list)):
        if ((pk_list[i] < updac) and (pk_list[i] > lodac)):
            dac_init.append(dac_list[i])
            pk_init.append(pk_list[i])
    #   first fit, use initial sample points
    try:
        slope_i, intercept_i = np.polyfit(dac_init, pk_init, 1)
    except:
        # we suggest here report an issue
        fig1, ax1 = plt.subplots()
        ax1.plot(dac_init, pk_init, marker='.')
        ax1.set_xlabel("DAC")
        ax1.set_ylabel("Peak Value")
        ax1.set_title("chan%d fail first gain fit" % chan)
        plt.tight_layout()
        plt.savefig(fp + 'fail_first_fit_ch%d.png' % chan)
        plt.close(fig1)
        print("fail at first gain fit")
        return 0, 0, 0
    #   with these filter, get a line and find the most line area
    y_min = pk_list[0]
    y_max = pk_list[-1]
    linear_dac_max = dac_list[-1]
    if 'CALI5' in fp or 'CALI6' in fp:
        inl_th = 0.01
    else:
        inl_th = 0.015
    index = len(dac_list) - 1
    for i in range(len(dac_list)):
        y_r = pk_list[i]
        y_p = dac_list[i] * slope_i + intercept_i
        inl = abs(y_r - y_p) / (y_max - y_min)
        if inl > inl_th:
            if dac_list[i] < 5:
                continue
            linear_dac_max = dac_list[i - 1]
            index = i
            break
    # print(linear_dac_max)
    # print(index)
    if index == 0:
        fig2, ax2 = plt.subplots(1, 2, figsize=(12, 6))
        ax2[0].plot(dac_list, pk_list, marker='.')
        ax2[0].set_xlabel("DAC")
        ax2[0].set_ylabel("Peak Value")
        ax2[0].set_title("chan%d fail linear range searching" % chan)
        tmp_inl = []
        tmp_dac = []
        for i in range(len(dac_list)):
            if dac_list[i] > updac:
                break
            y_r = pk_list[i]
            y_p = dac_list[i] * slope_i + intercept_i
            inl_1 = abs(y_r - y_p) / (y_max - y_min)
            tmp_inl.append(inl_1)
            tmp_dac.append(i)
        ax2[1].plot(tmp_dac, tmp_inl, marker='.')
        ax2[1].set_xlabel("DAC")
        ax2[1].set_ylabel("Peak Value")
        ax2[1].set_title("chan%d inl" % chan)
        plt.tight_layout()
        plt.savefig(fp + 'fail_inl_ch%d.png' % chan)
        plt.close(fig2)
        print("fail at first linear range searching: inl=%f for dac=0 is bigger than 0.03" % inl)
        return 0, 0, 0
    # print(dac_list[:index])
    #   second linear fit, with all linear area
    try:
        slope_f, intercept_f = np.polyfit(dac_list[1:index], pk_list[1:index], 1)
    except:
        fig3, ax3 = plt.subplots()
        ax3.plot(dac_list[1:index], pk_list[1:index], marker='.')
        ax3.set_xlabel("DAC")
        ax3.set_ylabel("Peak Value")
        ax3.set_title("chan%d fail second gain fit" % chan)
        plt.tight_layout()
        plt.savefig(fp + 'fail_second_fit_ch%d.png' % chan)
        plt.close(fig3)
        print("fail at second gain fit")
        return 0, 0, 0
    y_max = pk_list[index - 1]
    y_min = pk_list[1]
    INL = 0
    print(index)
    print(y_max)
    print(y_min)
    for i in range(1, index):
        y_r = pk_list[i]
        y_p = dac_list[i] * slope_f + intercept_f
        inl = abs(y_r - y_p) / (abs(y_max - y_min) * 1.5)
        print(inl)
        if inl * 100 > INL:
            INL = inl
    return slope_f, INL, linear_dac_max



def GetGain(fembs, fembNo, Cali_dict, savedir, fdir, namepat, snc, sgs, sts, dac_list, updac=25, lodac=10):
    global fname_1, ppk, bl, line_range_list, inl_list, gain_list
    log.tmp_log.clear()
    log.check_log.clear()
    log.chkflag.clear()
    log.badlist.clear()
    dac_v = {}  # mV/bit
    dac_v['4_7mVfC'] = 18.66
    dac_v['7_8mVfC'] = 14.33
    dac_v['14_0mVfC'] = 8.08
    dac_v['25_0mVfC'] = 4.61

    CC = 1.85 * pow(10, -13)
    e = 1.602 * pow(10, -19)
    # print(namepat)
    if "sgp1" in namepat:
        dac_du = dac_v['4_7mVfC']
        fname = '{}_{}_{}_sgp1'.format(snc, sgs, sts)
    else:
        dac_du = dac_v[sgs]
        fname = '{}_{}_{}'.format(snc, sgs, sts)

    pk_list = [[], [], [], []]
    channels_data = {}
    channels_data2 = {}
    sample_time = 1
    chn = 0
    for dac in dac_list:
        key_dict = namepat.format(snc, sgs, sts, dac) + '.bin'
        raw = Cali_dict[key_dict]
        rawdata = raw[0]
        pwr_meas = raw[1]
        wibdata = data_decode(rawdata, fembs)
        pldata = wibdata

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

        ref_chn = 7
        if 1:
            import matplotlib.pyplot as plt

            fig = plt.figure(figsize=(8, 6))
            plt.rcParams.update({'font.size': 14})
            rms = []
            mean = []
            std = []
            pkp = []

            for fe in [6]:  # [0, 1, 2, 3, 4, 5, 6, 7]:  # range(8):[0, 6]:#
                for fe_chn in [0, 1, 2, 3, 4, 5, 6, 7]:  #range(16): #[0, 1, 7]:  #[0, 2]:  # [9]:#
                    fechndata = np.array(datd[fe * 16 + fe_chn], dtype=np.int32)
                    rms.append(np.mean(fechndata))
                    rms_tmp = round(np.std(fechndata), 2)
                    maxpos = np.argmax(fechndata[100:]) + 100
                    minpos = np.argmin(fechndata[100:]) + 100
                    maxvalue = fechndata[maxpos]
                    minvalue = fechndata[minpos]
                    print(maxvalue)
                    print(minvalue)
                    baseline = np.mean(fechndata[maxpos - 30])
                    subaseline = [x - baseline for x in fechndata]
                    #
                    ch_mean = np.mean(fechndata)
                    ch_std = np.std(fechndata)
                    mean.append(ch_mean)
                    std.append(ch_std)
                    if np.mean(fechndata) > 2000:
                        print('chip: {}, channel: {}, mean = {}, std = {}'.format(fe, fe_chn, ch_mean, ch_std))
                    if fe_chn == 2:
                        plt.plot(range(len(fechndata)), fechndata, label="ch = {}".format(fe_chn), color='black')
                        channels_data[chn] = fechndata
                    if fe_chn == 3:
                        plt.plot(range(len(fechndata)), fechndata, label="ch = {}".format(fe_chn), color='black')
                        channels_data2[chn] = fechndata
                    else:
                        plt.plot(range(len(fechndata)), fechndata, label="ch = {}".format(fe_chn))

            chn += 1
            # labels = kmeans.predict(data_scaled)
            # print(kmeans.cluster_centers_)
            stdd = np.std(mean)
            yerr = stdd
            # plt.scatter(data[:, 0], data[:, 1],  cmap = 'viridis', s =50)
            m = np.mean(std)
            s = np.std(std)
        plt.title("board{} {}".format(fembNo, key_dict))
        plt.grid()
        plt.legend()
        # plt.tight_layout( rect=[0.05, 0.05, 0.95, 0.95])
        # plt.show()
        plt.close()

        for ifemb in fembs:
            fp = savedir[ifemb] + fdir
            if dac == 0:
                fname_1 = namepat.format(snc, sgs, sts, dac)
                ped, rms, _, _ = GetRMS(pldata, ifemb, fp, fname)
                ppk, bpk, bl = GetPeaks(pldata, ifemb, fp, fname_1, dac=dac)
                ppk_np = np.array(ppk) - np.array(bl)
                if not ('vdac' in fname_1):
                    pk_list[ifemb].append(ppk_np)
            else:
                fname_1 = namepat.format(snc, sgs, sts, dac)
                if ('vdac' in fname_1):
                    if not ('000mV' in fname_1):
                        ppk, bpk, bl = GetPeaks(pldata, ifemb, fp, fname_1, period=500, dac=dac)
                        # bl = 0
                else:
                    ppk, bpk, bl = GetPeaks(pldata, ifemb, fp, fname_1, dac=dac)
                ppk_np = np.array(ppk) - np.array(bl)
                pk_list[ifemb].append(ppk_np)

    print(channels_data)

    plt.figure(figsize=(12, 6))

    for chn, data in channels_data.items():
        plt.plot(range(len(data)), data, label=f"ch = {chn}", color = 'orange')
    for chn, data in channels_data2.items():
        plt.plot(range(len(data)), data, label=f"ch = {chn}", color = 'green')

    plt.title(f"Consolidated Plot for channel")
    plt.xlabel("Sample Index")
    plt.ylabel("ADC Value")
    plt.legend()
    plt.grid(True)
    plt.show()


    for ifemb in fembs:
        femb_id = "FEMB ID {}".format(fembNo['femb%d' % ifemb])
        tmp_list = pk_list[ifemb]
        new_pk_list = list(zip(*tmp_list))

        check = True
        check_issue = []
        dac_np = np.array(dac_list)
        pk_np = np.array(new_pk_list)
        fp = savedir[ifemb] + fdir

        gain_list = []
        inl_list = []
        inl_listcsv = []
        line_range_list = []
        max_dac_list = []

        #   overlap channel 0 pulse from [1 - 63]

        #   peak - dac linear
        for ch in range(128):
            uplim = np.max(pk_np[ch]) * 4 / 5
            lodac = np.max(pk_np[ch]) * 1 / 7
            print('--------------')
            print(ch)
            gain, inl, line_range = CheckLinearty(dac_np, pk_np[ch], uplim, lodac, ch, fp)
            if gain == 0:
                print("femb%d ch%d gain is zero" % (ifemb, ch))
            else:
                if ('vdac' in namepat):
                    gain = 1 / gain / 1000 * CC / e
                else:
                    gain = 1 / gain * dac_du / 1000 * CC / e
            gain_list.append(round(gain, 3))
            inl_list.append(inl)
            inl_listcsv.append(round(inl * 100, 2))
            line_range_list.append(round(line_range * dac_du / 1000 * 185))
            if ('vdac' in fname_1):
                if inl > 0.5:
                    check = False
                    check_issue.append("ch {} INL issue: {}".format(ch, inl))
                if line_range < 100:
                    check = False
                    check_issue.append("ch {} line range issue: {}".format(ch, line_range))
                if gain > 50:
                    check = False
                    check_issue.append("ch {} gain issue: {}".format(ch, gain))
            else:
                if inl > 0.01:
                    check = False
                    check_issue.append("ch {} INL issue: {}".format(ch, inl))
                if "900mV" in fname_1:
                    if 'sgp1' in fname_1:
                        if line_range < 4:
                            check = False
                            check_issue.append("ch {} line range issue: {}".format(ch, line_range))
                    else:
                        if line_range < 25:
                            check = False
                            check_issue.append("ch {} line range issue: {}".format(ch, line_range))
                    if gain > 43:
                        check = False
                        check_issue.append("ch {} Gain issue at 14_0 mVfC: {}".format(ch, line_range))

                elif '200mV' in fname_1:
                    if 'sgp1' in fname_1:
                        if line_range < 20:
                            check = False
                            check_issue.append("ch {} Line range issue lower than 20: {}".format(ch, line_range))
                    else:
                        if line_range < 48:
                            check = False
                            check_issue.append("ch {} Line range issue lower than 50: {}".format(ch, line_range))
                    if '4_7' in fname_1:
                        if gain > 135:
                            check = False
                            check_issue.append("ch {} Gain issue at 4_7 mVfC: {}".format(ch, line_range))
                    if '7_8' in fname_1:
                        if gain > 78:
                            check = False
                            check_issue.append("ch {} Gain issue at 7_8 mVfC: {}".format(ch, line_range))
                    if '14_0' in fname_1:
                        if gain > 45:
                            check = False
                            check_issue.append("ch {} Gain issue at 14_0 mVfC: {}".format(ch, line_range))
                    if '25_0' in fname_1:
                        if gain > 26:
                            check = False
                            check_issue.append("ch {} Gain issue at 25_0 mVfC: {}".format(ch, line_range))

            # max_dac_list.append(max_dac)
        log.tmp_log[femb_id]["INL"] = np.max(inl_list)
        log.tmp_log[femb_id]["Gain"] = np.mean(gain_list)
        log.tmp_log[femb_id]["Gainstd"] = np.std(gain_list)
        log.tmp_log[femb_id]["Linearangemin"] = np.min(line_range_list)
        log.check_log[femb_id]["Result"] = check
        log.check_log[femb_id]["Issue List"] = check_issue

        log.tmp_log[ifemb]["inl_list"] = inl_listcsv
        log.tmp_log[ifemb]["gain_list"] = gain_list
        log.tmp_log[ifemb]["line_range_list"] = line_range_list






fembs = [2]
FE_Baseline = "200mVBL"
FE_Gain = "14_0mVfC"
FE_Peak_time = "2_0us"

dac_list = range(0,64,1) # other dac_list = range(0, 64, 8)

datadir = 'D:/FEMB_Debug_Mode/CTS_QC/tmp_data_cali_analysis_doc/'
savedir = 'D:/FEMB_Debug_Mode/CTS_QC/tmp_data_cali_analysis_doc/'
f_pwr = datadir + "QC_Cali01_t6.bin"
with open(f_pwr, 'rb') as fn:
    Cali01_dict = pickle.load(fn)
print(len(Cali01_dict))
print(type(Cali01_dict))
keys_list = list(Cali01_dict.keys())
print(keys_list)
a = Cali01_dict['CALI1_SE_200mVBL_14_0mVfC_2_0us_0x00.bin'] # a[0] = data; a[1] = none; a[2] = configuration; a[3] = Test_log_info

print(a[3]['femb id'])

GetGain(fembs, a[3]['femb id'], Cali01_dict, savedir, "CALI1/", "CALI1_SE_{}_{}_{}_0x{:02x}", "200mVBL", "4_7mVfC", "2_0us", dac_list = range(0,64,8), updac=25, lodac=10)