from wib_cfgs import WIB_CFGS
import time
import sys
import numpy as np
import pickle
import copy
import os
import time, datetime, random, statistics
import subprocess
import QC_components.qc_function as a_func
import QC_components.qc_log as log









class QC_Runs:
    def __init__(self, fembs, sample_N=1):
        self.fembs = fembs
        self.sample_N = sample_N
        self.fembNo={}
        self.fembName={}
        self.vgndoft = 0
        self.vdacmax = 0.5
        self.vstep = 10
        self.chk = WIB_CFGS()
        self.LAr_Dalay = 5
        self.sdd0 = 0
        self.sdf0 = 0
        self.sncs = ["900mVBL", "200mVBL"]
        self.sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]
        self.pts = ["1_0us", "0_5us",  "3_0us", "2_0us"]

        ####### Test enviroment logs #######

        self.logs={}

        tester=input("please input your name:  ")
        self.logs['tester']=tester
        env_cs = input("Test is performed at cold(LN2) (Y/N)? : ")
        if ("Y" in env_cs) or ("y" in env_cs):
            env = "LN"
        else:
            env = "RT"
        self.logs['env']=env

        ToyTPC_en = input("ToyTPC at FE inputs (Y/N) : ")
        if ("Y" in ToyTPC_en) or ("y" in ToyTPC_en):
            toytpc = "150pF"
        else:
            toytpc = "0pF"
        self.logs['toytpc']=toytpc

        note = input("A short note (<200 letters):")
        self.logs['note']=note

        for i in self.fembs:
            self.fembNo['femb{}'.format(i)]=input("FEMB{} ID: ".format(i)).strip()

        self.logs['femb id']=self.fembNo
        self.logs['date']=datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        log.report_log00 = self.logs    ### report
        ####### Create data saving directory #######

        save_dir = "./QC"
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except OSError:
                print("Error to create folder %s" % save_dir)
                sys.exit()

        self.save_dir = save_dir+"/"

        fp = self.save_dir + "logs_env.bin"
        with open(fp, 'wb') as fn:
             pickle.dump(self.logs, fn)









    def pwr_fembs(self, status):

        #self.chk = WIB_CFGS()
        self.chk.wib_fw()
        self.chk.fembs_vol_set(vfe=3.0, vcd=3.0, vadc=3.5)

        if status=='on':
            print("Turning on FEMBs")
            self.chk.femb_powering(self.fembs)
            pwr_meas = self.chk.get_sensors()
        if status=='off':
            print("Turning off FEMBs")
            self.chk.femb_powering([])







    def check_pwr_off(self, pwr_data):
        pwr_sts = True
        for i in self.fembs:
           bias_v = pwr_data['FEMB%d_BIAS_V'%i]
           fe_v = pwr_data['FEMB%d_DC2DC0_V'%i]
           cd_v = pwr_data['FEMB%d_DC2DC1_V'%i]
           adc_v = pwr_data['FEMB%d_DC2DC2_V'%i]
           print (bias_v, fe_v, cd_v, adc_v)

           if (bias_v < 3.0) and (fe_v < 0.5) and (cd_v < 0.5) and (adc_v < 0.5):
               print ("FEMB {} is turned off".format(i))
           else:
               pwr_sts = False
        return pwr_sts






    def take_data(self, sts=0, snc=0, sg0=0, sg1=0, st0=0, st1=0, dac=0, fp=None, sdd=0, sdf=0, slk0=0, slk1=0, sgp=0,  pwr_flg=False, swdac=1, adc_sync_pat=False, bypass = False, autocali=0, excali = False):

        cfg_paras_rec = [] # record the configuration
        ext_cali_flg = False
        datad = {}

        self.chk.adcs_paras = [ # c_id, data_fmt(0x89), diff_en(0x84), sdc_en(0x80), vrefp, vrefn, vcmo, vcmi,
                            [0x4, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0x5, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0x6, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0x7, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0x8, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0x9, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0xA, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                            [0xB, 0x08, 0, 0, 0xDF, 0x33, 0x89, 0x67, autocali],
                          ]
        if sts == 1 :
            if swdac==1: #internal ASIC-DAC is enabled
                self.chk.set_fe_board(sts=sts,snc=snc,sg0=sg0,sg1=sg1, st0=st0, st1=st1, swdac=1, dac=dac, sdd=sdd,sdf=sdf,slk0=slk0,slk1=slk1,sgp=sgp)
                adac_pls_en = 1
            elif swdac==2: #external DAC is enabled
                self.chk.set_fe_board(sts=sts,snc=snc,sg0=sg0,sg1=sg1, st0=st0, st1=st1, swdac=2, dac=dac, sdd=sdd,sdf=sdf,slk0=slk0,slk1=slk1,sgp=sgp)
                adac_pls_en = 0
                ext_cali_flg = True
        else:
            self.chk.set_fe_board(sts=sts, snc=snc, sg0=sg0, sg1=sg1, st0=st0, st1=st1, swdac=0, dac=0x0, sdd=sdd,sdf=sdf,slk0=slk0,slk1=slk1,sgp=sgp)
            adac_pls_en = 0

        if adc_sync_pat:
            for i in range(8):
                if bypass:
                    self.chk.adcs_paras[i][1] = self.chk.adcs_paras[i][1]|0x20
                else:
                        self.chk.adcs_paras[i][1] = self.chk.adcs_paras[i][1]|0x10
        for femb_id in self.fembs:
            if sdd==1:
                self.chk.adc_flg[femb_id] = True
                for i in range(8):
                    self.chk.adcs_paras[i][2]=1   # enable differential

            if adc_sync_pat:
                self.chk.adc_flg[femb_id] = True

            self.chk.fe_flg[femb_id] = True
            cfg_paras_rec.append( (femb_id, copy.deepcopy(self.chk.adcs_paras), copy.deepcopy(self.chk.regs_int8), adac_pls_en) )
            self.chk.femb_cfg(femb_id, adac_pls_en )
        if (sdd == 1) or (sdf == 1) or (sgp == 1):
            print ("warning: extra 3.5 delay for DIFF and SE_ON after configuration")
            time.sleep(self.LAr_Dalay)
        #self.sdd0 = sdd
        #self.sdf0 = sdf
        if autocali&0x01:
            time.sleep(0.5)
            for femb_id in self.fembs:
                self.chk.femb_autocali_off(femb_id)
        else:
            time.sleep(0.1) #temperary

        if self.chk.align_flg == True:
            self.chk.data_align(self.fembs)
            self.chk.align_flg = False
            time.sleep(0.001)

        # self.chk.wib_pls_gen(fembs=self.fembs, cp_period=500, cp_phase=0, cp_high_time=0)
        #self.chk.wib_mon_switches(dac0_sel=0, dac1_sel=0, dac2_sel=0, dac3_sel=0, mon_vs_pulse_sel=1, inj_cal_pulse=1)
        for femb_id in self.fembs:
            self.chk.femb_cd_gpio(femb_id=femb_id, cd1_0x26=0x02, cd1_0x27=0x1f, cd2_0x26=0x00, cd2_0x27=0x1f)

        if pwr_flg==True:
            time.sleep(0.5)
            pwr_meas = self.chk.get_sensors()
            sps = 10
            vold = self.chk.wib_vol_mon(femb_ids=self.fembs,sps=sps)
            pwr_meas["Powerrails"] = vold
        else:
            time.sleep(0.01)
            pwr_meas = None

        if autocali&0x01:
            return  None
        if dac == 0:
            time.sleep(self.LAr_Dalay)
        if ext_cali_flg:
            if excali == False:
                datae = {}
                print ("Calibration with pulser from WIB starts...")
                cp_period = 500
                vdacmax=self.vdacmax
                vdacs = np.arange(vdacmax,self.vgndoft,-(vdacmax-self.vgndoft)/self.vstep)
                dac0_sel = 0
                dac1_sel = 0
                dac2_sel = 0
                dac3_sel = 0
                for vdac in vdacs:
                    self.chk.wib_cali_dac(dacvol=vdac)
                    for femb_id in self.fembs:
                        if femb_id == 0:
                            dac0_sel=1
                        if femb_id == 1:
                            dac1_sel=1
                        if femb_id == 2:
                            dac2_sel=1
                        if femb_id == 3:
                            dac3_sel=1
                    self.chk.wib_mon_switches(dac0_sel, dac1_sel, dac2_sel, dac3_sel, mon_vs_pulse_sel=1, inj_cal_pulse=1)
                    cp_high_time = int(cp_period*32*7/8)
                    self.chk.wib_pls_gen(fembs=self.fembs, cp_period=cp_period, cp_phase=0, cp_high_time=cp_high_time)
                    for femb_id in self.fembs:
                        self.chk.femb_cd_gpio(femb_id=femb_id, cd1_0x26=0x00, cd1_0x27=0x1f, cd2_0x26=0x00, cd2_0x27=0x1f)
                    time.sleep(0.01)
                    rawdata = self.chk.spybuf_trig(fembs=self.fembs, num_samples=self.sample_N,trig_cmd=0)
                    fplocal = fp[0:-4] + "_vdac%06dmV"%(int((vdac+0.0001)*1000))+fp[-4:]
                    # with open(fplocal, 'wb') as fn:
                    #     pickle.dump( [rawdata, pwr_meas, cfg_paras_rec, self.logs, vdac], fn)
                    fsubdirs = fplocal.split("/")
                    print(fsubdirs)
                    print(fsubdirs[-1])
                    datad[fsubdirs[-1]] = [rawdata, pwr_meas, cfg_paras_rec, self.logs]
                self.chk.wib_pls_gen(fembs=self.fembs, cp_period=cp_period, cp_phase=0, cp_high_time=0)
                self.chk.wib_mon_switches() #close wib_mon
            else:
                time.sleep(0.5)
                dac0_sel = 0
                dac1_sel = 0
                dac2_sel = 0
                dac3_sel = 0
                for x in [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]:
                    dacvol = x * 0.05
                    self.chk.wib_cali_dac(dacvol=dacvol)
                    for fembid in self.fembs:
                        if fembid == 0:
                            dac0_sel = 1
                        if fembid == 1:
                            dac1_sel = 1
                        if fembid == 2:
                            dac2_sel = 1
                        if fembid == 3:
                            dac3_sel = 1
                    self.chk.wib_mon_switches(dac0_sel=dac0_sel, dac1_sel=dac1_sel, dac2_sel=dac2_sel, dac3_sel=dac3_sel, mon_vs_pulse_sel=1, inj_cal_pulse=0)
                    print('DAC value: {}'.format(dacvol))
                    # input('debug dac, enable route')
                    cp_period = 500
                    cp_high_time = int(cp_period * 32 * 1 / 8)
                    # cp_high_time = int(cp_period*32*1/2)
                    self.chk.wib_pls_gen(fembs=self.fembs, cp_period=cp_period, cp_phase=0, cp_high_time=cp_high_time, inj_cal_pulse_sw=1)
                    # input('debug pulse enable')
                    for femb_id in self.fembs:
                        self.chk.femb_cd_gpio(femb_id=femb_id, cd1_0x26=0x00, cd1_0x27=0x1f, cd2_0x26=0x00, cd2_0x27=0x1f)
                    # input('debug enable FEMB external pulse route')
                    time.sleep(0.01)
                    ####################FEMBs Data taking################################
                    rawdata = self.chk.spybuf_trig(fembs=self.fembs, num_samples=self.sample_N, trig_cmd=0)
                    fplocal = fp[0:-4] + "_vdac%06dmV" % (int((dacvol + 0.0001) * 1000)) + fp[-4:]
                    with open(fplocal, 'wb') as fn:
                        pickle.dump( [rawdata, pwr_meas, cfg_paras_rec, self.logs, x], fn)
                    fsubdirs = fplocal.split("/")
                    print(fsubdirs)
                    print(fsubdirs[-1])
                    datad[fsubdirs[-1]] = [rawdata, pwr_meas, cfg_paras_rec, self.logs]
                self.chk.wib_mon_switches()  # close wib_mon

        else:
            rawdata = self.chk.spybuf_trig(fembs=self.fembs, num_samples=self.sample_N,trig_cmd=0)

            with open(fp, 'wb') as fn:
                pickle.dump( [rawdata, pwr_meas, cfg_paras_rec, self.logs], fn)
            # datad = [rawdata, pwr_meas, cfg_paras_rec, self.logs]
        return datad


    def femb_leakage_debug(self):
        datad = {}
        datadir = self.save_dir + "Leakage_Current/"
        try:
            os.makedirs(datadir)
        except OSError:
            print("Error to create folder %s !!! Continue to next test........" % datadir)
            return
        snc = 1  # 200 mV
        sg0 = 0
        sg1 = 0  # 14mV/fC
        st0 = 1
        st1 = 1  # 2us
        dac = 0x20
        sts = 1
        ####### 500 pA #######
        self.chk.femb_cd_rst()
        self.sample_N = 5
        fp = datadir + "LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "500pA")
        datad["LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "500pA")] = self.take_data(sts, snc, sg0, sg1, st0, st1, dac, fp, slk0=0, slk1=0, pwr_flg=False)
        ####### 100 pA #######
        # self.chk.femb_cd_rst()
        fp = datadir + "LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "100pA")
        datad["LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "100pA")] = self.take_data(sts, snc, sg0, sg1, st0, st1, dac, fp, slk0=1, slk1=0, pwr_flg=False)
        ####### 5 nA #######
        # self.chk.femb_cd_rst()
        fp = datadir + "LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "5nA")
        datad["LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "5nA")] = self.take_data(sts, snc, sg0, sg1, st0, st1, dac, fp, slk0=0, slk1=1, pwr_flg=False)
        ####### 1 nA #######
        # self.chk.femb_cd_rst()
        fp = datadir + "LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "1nA")
        datad["LC_SE_{}_{}_{}_0x{:02x}_{}.bin".format("200mVBL", "14_0mVfC", "2_0us", 0x20, "1nA")] = self.take_data(sts, snc, sg0, sg1, st0, st1, dac, fp, slk0=1, slk1=1, pwr_flg=False)








    def femb_chk_pulse(self):
        datadir = self.save_dir+"CHK/"
        datad = {}
        try:
            os.makedirs(datadir)
        except OSError:
            print ("Error to create folder %s !!! Continue to next test........"%datadir)
            return

        sncs = self.sncs
        sgs = self.sgs
        pts = self.pts

        dac = 0x10
        sts = 1

        self.chk.femb_cd_rst()
        self.sample_N = 1
        for snci in range(2):
            for sgi in  range(4):
                sg0 = sgi%2
                sg1 = sgi//2
                for sti in range(4):
                    st0 = sti%2
                    st1 = sti//2
#   SE  2*4*4 = 32  {[snc 200/900 mV] * [sg 4.7/7.8/14/25 mV/fC] * [st 0.5/1/2/3 us]}
                    fp = datadir + "CHK_SE_{}_{}_{}_0x{:02x}.bin".format(sncs[snci],sgs[sgi],pts[sti],dac)
                    datad["CHK_SE_{}_{}_{}_0x{:02x}.bin".format(sncs[snci],sgs[sgi],pts[sti],dac)] = self.take_data(sts, snci, sg0, sg1, st0, st1, dac, fp, pwr_flg=False)

        print('SEON pulse')
        sg1 = 0;    sg0 = 0     # 14 mV/fC
        st1 = 1;    st0 = 1     # 2 us
        self.chk.femb_cd_rst()
        self.sample_N = 1
        for snci in range(2):
#   SEON    2   {[snc 200/900 mV] * [sg 14 mV/fC] * [st 2 us]}  sdf = 1
                    fp = datadir + "CHK_SEON_{}_{}_{}_0x{:02x}.bin".format(sncs[snci], sgs[0], pts[3], dac)
                    datad["CHK_SEON_{}_{}_{}_0x{:02x}.bin".format(sncs[snci], sgs[0], pts[3], dac)] = self.take_data(sts, snci, sg0, sg1, st0, st1, dac, fp, sdf = 1, pwr_flg=False)


        print('Differential Pulse')
#   DIFF    2       {[snc 200/900 mV] * [14 mV/fc] *[2 us]}
        sg1 = 0;    sg0 = 0     # 14 mV/fC
        st1 = 1;    st0 = 1     # 2 us
        self.chk.femb_cd_rst()
        cfg_paras_rec = []
        for i in range(8):
            self.chk.adcs_paras[i][2] = 1    # enable differential interface
        #self.chk.set_fe_board(sts=1, snc=0, sg0=sg0, sg1=sg1, st0=st0, st1=st1, sdd=1, swdac=1, dac=0x10)
        self.sample_N = 1
        for snci in range(2):
                    fp = datadir + "CHK_DIFF_{}_{}_{}_0x{:02x}.bin".format(sncs[snci], sgs[0], pts[3], dac)
                    datad["CHK_DIFF_{}_{}_{}_0x{:02x}.bin".format(sncs[snci], sgs[0], pts[3], dac)] = self.take_data(sts, snci, sg0, sg1, st0, st1, dac, fp, sdd = 1, pwr_flg=False, swdac = 1)
                                #time.sleep(0.5)
        for i in range(8):
            self.chk.adcs_paras[i][2] = 0    # disable differential interface


        print('SGP pulse response')
        #   SGP    4       {[snc 200 mV] * [4.7 7.8 14 25 mV/fc] *[2 us]}
        st1 = 1
        st0 = 1  # 2 us
        sts = 1
        self.chk.femb_cd_rst()
        cfg_paras_rec = []
        for i in range(8):
            self.chk.adcs_paras[i][2] = 1  # enable differential interface
        # self.chk.set_fe_board(sts=1, snc=0, sg0=sg0, sg1=sg1, st0=st0, st1=st1, sdd=1, swdac=1, dac=0x10)
        self.sample_N = 1
        for sgi in range(4):    # adjust Gain 4.7 7.8 14 25 mV/fc
            sg0 = sgi % 2
            sg1 = sgi // 2
            fp = datadir + "CHK_SGP_{}_{}_{}_0x{:02x}.bin".format(sncs[1], sgs[sgi], pts[3], dac)
            datad["CHK_SGP_{}_{}_{}_0x{:02x}.bin".format(sncs[1], sgs[sgi], pts[3], dac)] = self.take_data(sts, snci, sg0, sg1, st0, st1, dac, fp, sgp=1, pwr_flg=False)


#       External Pulse
        print('External pulse')

        snc = 1 # 200 mV BL
        sg0 = 0
        sg1 = 0 # 14_0 mv/fC
        st0 = 1
        st1 = 1 # 2 us
        sts = 1
        dac=0
        self.chk.femb_cd_rst()
        self.sample_N = 1
        fp = datadir + "CHK_EX_{}_{}_{}.bin".format("200mVBL","14_0mVfC","2_0us")
        datad.update(self.take_data(sts, snc, sg0, sg1, st0, st1, dac, fp, swdac=2, pwr_flg=False))

        fp = datadir + "femb_chk_pulse_t4" + ".bin"
        with open(fp, 'wb') as fn:
            pickle.dump(datad, fn)

