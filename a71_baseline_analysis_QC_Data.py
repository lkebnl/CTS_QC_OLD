import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import csv
import sys
import time
import glob
from QC_tools import ana_tools
import QC_check
from fpdf import FPDF
import argparse
import Path as newpath
import components.item_report as item_report
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from PIL import Image
import QC_components.qc_a_function as a_func
import QC_components.qc_log as log
import QC_components.All_Report as a_repo
import QC_components.QC_CSV_Report as csv_repo
# use webbrowser to show the issue report
import webbrowser
import QC_components.qc_log as main_dict
import numpy as np
import matplotlib.pyplot as plt
import re, numpy as np, matplotlib.pyplot as plt, pandas as pd
from scipy.signal import welch, detrend
from matplotlib.backends.backend_pdf import PdfPages


csv_data = {}
csv_file = 'femb_info.csv'
file_path = r'.\femb_info.csv'
with open(csv_file, mode='r', newline='', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) == 2:
            key, value = row
            csv_data[key.strip()] = value.strip()
main_dict.top_path = csv_data['top_path']
top_path = main_dict.top_path


class QC_reports:

    def __init__(self, fdir, fembs=[], NewWIB=True):
        print(fdir.split("/"))
        self.datadir = fdir + "/"
        self.report_source_doc = 0
        fp = self.datadir + "logs_env.bin"
        with open(fp, 'rb') as fn:
            logs = pickle.load(fn)
        log.report_log00 = dict(logs)
        logs["datadir"] = self.datadir
        self.logs = logs
        self.fembsName = {}
        self.fembsID = {}
        self.NewWIB = NewWIB
        if fembs:
            self.fembs = fembs
            for ifemb in fembs:
                self.fembsName[f'femb{ifemb}'] = logs['femb id'][f'femb{ifemb}']
                self.fembsID[f'femb{ifemb}'] = ifemb
        else:
            # self.fembsID = logs['femb id']
            self.fembs = []
            for key, value in logs['femb id'].items():
                self.fembs.append(int(key[-1]))
            for ifemb in self.fembs:
                self.fembsName[f'femb{ifemb}'] = logs['femb id'][f'femb{ifemb}']
                self.fembsID[f'femb{ifemb}'] = ifemb
        self.savedir = {}
        print("Will analyze the following fembs: ", self.fembs)

    def Gather_PNG_PDF(self, fdir):
        # input_folder_path = fdir + '/path/to/your/png/files'
        output_pdf_path = fdir + '/report.pdf'
        png_files = [f for f in os.listdir(fdir) if f.endswith('.png')]
        c = canvas.Canvas(output_pdf_path, pagesize=letter)
        # image_count = 0  # 记录已经处理的图像数量
        current_page = 0  # 记录当前页数
        for i, png_file in enumerate(png_files):
            png_path = os.path.join(fdir, png_file)
            img = Image.open(png_path)
            # 通过 drawImage 将图像添加到 PDF 文件
            remainder = i % 4
            c.drawImage(png_path, 0, 600 - remainder * 160, width=img.width * 160 / img.height, height=40 * 4)
            if remainder == 3:
                c.showPage()  # 开始新的一页
            current_page += 1
        c.save()

    # 1     Power Consumption
    # ================================================================================================

    def RMS_report(self):
        log.test_label.append(5)
        datadir = self.datadir + "RMS/"

        f_pwr = datadir + "QC_femb_rms_t5.bin"
        with open(f_pwr, 'rb') as fn:
            femb_rms_dict = pickle.load(fn)

        section_status = True
        check = [True, True, True, True]
        check_list = [0, 1, 2, 3]
        # datafiles = sorted(glob.glob(datadir+"RMS*.bin"), key=os.path.getmtime)
        for afile in femb_rms_dict.keys():
            print(afile)
            # with open(afile, 'rb') as fn:
            #     raw = pickle.load(fn)

            if ("200" in afile) and ("14" in afile) and ("0_5us" in afile) and ("SE_" in afile):
                print("analyze file: %s" % afile)
                raw = femb_rms_dict[afile]
                rawdata = raw[0]
                if '\\' in afile:
                    fname = afile.split("\\")[-1][4:-9]
                else:
                    fname = afile.split("/")[-1][4:-9]
                qc = ana_tools()
                pldata = qc.data_decode(rawdata, self.fembs)
                for ifemb in self.fembs:
                    print(ifemb)
                    mean = 0
                    datdi = [0, 1, 2, 3, 4]
                    fechndata = []
                    for i in range(5):
                        wibdatai = pldata[i]
                        datdi[i] = [wibdatai[0], wibdatai[1], wibdatai[2], wibdatai[3]][ifemb]
                    datd = np.concatenate((datdi[0], datdi[1], datdi[2], datdi[3], datdi[4]), axis=1)
                    print(datd)
                    import matplotlib.pyplot as plt

                    fig = plt.figure(figsize=(24, 6))
                    plt.rcParams.update({'font.size': 14})
                    rms = []
                    mean = []
                    std = []
                    pkp = []
                    chn = 0
                    channels_data = [None] * 128
                    # for fe in [0, 1, 2, 3, 4, 5, 6, 7]:  # range(8):[0, 6]:#
                    # Open a PDF file to save plots
                    with PdfPages("channel_plots.pdf") as pdf:
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

                                # === Time Series Plot ===
                                plt.figure(figsize=(12, 4))
                                if ch_mean > 2000:
                                    print('chip: {}, channel: {}, mean = {}, std = {}'.format(fe, fe_chn, ch_mean,
                                                                                              ch_std))
                                    print('channel number = {}'.format(fe * 16 + fe_chn))
                                plt.plot(range(len(fechndata)), fechndata,
                                         label='Chip: {}; Channel: {}'.format(fe, fe_chn))
                                plt.title("Waveform - Chip: {}; Channel: {}".format(fe, fe_chn), fontsize=10)
                                plt.xlabel("{} slot{}".format(datadir, ifemb), fontsize=10)
                                plt.ylabel("ADC Counts")
                                plt.ylim(ch_mean - 200, ch_mean + 200)
                                plt.grid()
                                plt.legend(fontsize=8)
                                plt.tight_layout()
                                pdf.savefig()  # Save this figure to the PDF
                                plt.close()

                                # === Histogram Plot ===
                                plt.figure(figsize=(12, 4))
                                plt.xlim(500, 1600)
                                plt.hist(fechndata, bins=100, color='skyblue', edgecolor='black')
                                plt.title("Histogram - Chip: {}; Channel: {}; RMS: {}".format(fe, fe_chn, rms_tmp), fontsize=10)
                                plt.xlabel("Amplitude")
                                plt.ylabel("Frequency")
                                plt.grid()
                                plt.tight_layout()
                                pdf.savefig()  # Save this figure to the PDF
                                plt.close()

                                # Save raw data
                                channels_data[chn] = fechndata
                                chn += 1

                        # # 參數設定
                            # # === 原始 FFT 頻譜 ===
                            # xd = detrend(fechndata, type='constant')
                            # X = np.fft.fft(xd)  # 對去均值後的數據做 FFT
                            # Fs = 2e6
                            # freqs = np.fft.fftfreq(len(xd), d=1/Fs)  # 頻率軸 (歸一化, d=1/Fs)
                            # # 只取正頻率部分
                            # half = len(xd) // 2
                            # freqs = freqs[:half]
                            # mag = np.abs(X[:half]) / len(xd)  # 幅度歸一化
                            # # plt.figure(figsize=(24, 6))
                            # plt.figure()
                            # plt.plot(freqs, mag)
                            # plt.title("FFT magnitude spectrum")
                            # plt.xlabel("cycles / sample")  # 若有 Fs，改成 Hz
                            # plt.ylabel("Amplitude (arb.)")
                            # plt.tight_layout()
                            # plt.show()
                            # plt.close()

                            # labels = kmeans.predict(data_scaled)
                    # print(kmeans.cluster_centers_)


print('\n')
print('- Back Up For Debug -------------------------------------------')
print('mapping to FEMB                          chip channel: ._[15:0]')
print('front:  chip_1_U07   chip_0_u03        chip_4_u19    chip_5_u21')
print('bottom: chip_3_U17   chip_2_u11        chip_6_u23    chip_7_u25')
print('---------------------------------------------------------------')
                    # mapping




# fdir = "D:/FEMB_Debug_Mode/BNL_CE_WIB_SW_QC/tmp_data/05_15_03_49_CTS_BNL_S0BNL_FEMB_IO-1865-1K_00001_S1BNL_FEMB_IO-1865-1K_00005_LN_QC/QC/"
fdir = "/home/dune/Documents/Debug_Hub/1865-1K-40/QC/"
fdir = fdir.replace("\\", "/")
rp = QC_reports(fdir, [0], NewWIB = True)
rp.RMS_report()