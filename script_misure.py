import serial
import sys
import time
import glob
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import datetime

clock_period = (1/66.6)*1E-6 #in secondi
shap = '11' #triangolare
ampl_scelta = 3
#freq_list = [2,5,10,20,50,80,100,150,200,400,600,1500,2500,3500,8000]
freq_list = [2,5,10,20,50,100,150,200,300,500,800,1000,1500,2500,3000,5000,8000]
prescaler_list = [128,64,32,16]
BAUDRATE = 57600
num_points_acq = 100000

num_samples_arduino = 3500
bits_ADC = 10
INL0 = 0 #parametro da definire!
V_range = 5000.0 #in mV

def generate_bytes(clock_period,shape,ampl,frequency):
    bin_ampl = format(ampl, '03b')
    byte1 = '0b00%s0%s'%(shape,bin_ampl)
    byte1_int = int(byte1,2)
    #frequency = float(input("frequenza onda (2 - 8000 Hz): "))
    periodo_sec = 1.0/frequency
    periodo_clk_counts = periodo_sec/clock_period
    clock_per_count = int(periodo_clk_counts/(2*4095))
    count_clock = 1/(frequency * (4095*2*clock_period))
    byte3_int = clock_per_count >> 6
    byte2_int = clock_per_count - (byte3_int << 6)
    #print (frequency)
    #print ("byte1: %s"%byte1_int)
    #print ("byte2: %s"%byte2_int)
    #print ("byte3: %s"%byte3_int)
    bytes = [chr(byte1_int),chr(byte2_int),chr(byte3_int)]
    periodo = clock_period*clock_per_count*1E3*4095.0*2.0 #in ms
    print ("colpi clock ad ogni incremento: %s"%clock_per_count)
    print ("periodo: %f ms"%periodo)
    print ("frequenza: %f kHz"%(1/periodo))
    return bytes,clock_per_count

def find_port(maker_str):
    ports = list(serial.tools.list_ports.comports())
    port = 0
    for p in ports:
        if maker_str in p.manufacturer:
            port = p.device
    if port != 0:
        return port
    else:
        print ("errore apertura seriale %s"%maker_str)
        sys.exit(1)

def read_data_file(data_file):
    with open(data_file,'r') as f:
        data_list_int = [int(x) for x in f.readlines()]
    return data_list_int

def calc_DNL(list_bin_norm):
    P_D = 1.0/len(list_bin_norm)
    DNL = []
    for Counts_D in list_bin_norm:
        DNL_D = (Counts_D - P_D)*V_range
        #print (DNL_D)
        DNL.append(DNL_D) #dnl in millivolt
    return DNL

def calc_INL(list_dnl):
    DNL = list_dnl
    INL = []
    for i_d,dnl in enumerate(DNL):
        INL_D = 0.0
        for j in range(i_d):
            INL_D = INL_D + DNL[j]
        INL_D = INL_D - DNL[i_d]/2.0 - DNL[0]/2.0 + INL0
        INL.append(INL_D)
    return INL

def list_central_points(bin_counts,bins_edges):
    bin_central = []
    for i,value in enumerate(bin_counts):
        central = (bins_edges[i] + bins_edges[i+1])/2.0
        bin_central.append(central)
    return bin_central
    
def plot_graph(int_list,code_to_search,file_to_save):
    fig, axes = plt.subplots(2, 2)
    bins_list = list(range(1,1024)) #da 1 a 1023 compreso
    for i,x in enumerate(bins_list): #da -0.5 a 1022.5 compresi
        bins_list[i] = x - 0.5
    bin_values, bins_edges, null= axes[1][0].hist(int_list,
                                               bins=bins_list, 
                                               density=True,
                                               alpha=0.80)
    #num_bins = len(bin_values)
    #print (np.sum(bin_values) #per vedere se l'istogramma e' normalizzato)
    DNL = calc_DNL(bin_values) #in mV
    DNL_LSB = [x/(5000.0/1024) for x in DNL] #trasformazione in LSB
    INL = calc_INL(DNL_LSB)                  #gia' in LSB (credo... ripensarci)
    
    print (max([abs(x) for x in DNL_LSB]))
    print (max([abs(x) for x in INL]))
    bin_central = list_central_points(bin_values,bins_edges)

    #codes = search_code(int_list,code_to_search)
    #num_max_camp = codes[-1]-codes[0]
    #print ("numero di campionamenti tra il primo e l'ultimo codice %s trovati = %s"%()
    #                                                            code_to_search,num_max_camp)
    #for i,code in enumerate(codes):
    #    axes[0][0].axvline(x=code)
    #    if i>0:
    #        num_camp = code - codes[i-1]
    ##        print ("numero di campionamenti tra due codici %s successivi: %s"%(code_to_search,num_camp))
    axes[0][0].plot(list(range(len(int_list))), int_list,
                    linewidth=1, markersize=2,
                    alpha=0.80)
    axes[0][1].plot(bin_central,DNL_LSB,
                    linewidth=1, markersize=2,
                    alpha=0.80)
    axes[1][1].plot(bin_central,INL,
                    linewidth=1, markersize=2,
                    alpha=0.80)
    axes[1][0].set_ylabel('Probabilita')
    axes[1][0].set_title('istogramma normalizzato')
    axes[1][0].set_xlabel('Codice ADC')
    axes[1][1].set_xlabel('Codice ADC')
    axes[1][1].set_ylabel('LSB')
    axes[0][1].set_ylabel('LSB')
    axes[0][0].set_ylabel('codice adc')
    #axes[0][1].set_ylabel('DNL')
    #axes[1][0].set_title('Probabilita')
    axes[0][1].set_title('DNL')
    axes[1][1].set_title('INL')
    fig.savefig(file_to_save, dpi=fig.dpi)
    fig.close('all')
    #plt.show()

def search_code(wave_list,value):
    x_points = []
    last_index = 0
    for i, data in enumerate(wave_list):
        if data == value:
            x_points.append(i)
            last_index = i
    return x_points

def arduino_sampling(prescaler):
    ard = serial.Serial(find_port("Arduino"),BAUDRATE,timeout=5)
    time.sleep(10)
    toSend = "%s#"%prescaler #il programma arduino richiede # come carattere finale
    try:
        ard.write(toSend)
        time.sleep(1)
        line_int = []
        freq_acq = []
        print ("acquisizione %s punti"%num_points_acq)
        ard.reset_input_buffer()
        ard.reset_output_buffer()
        time.sleep(0.2)
        for index in range(num_points_acq):
            str = ard.readline().strip()
            #print ("letto %s"%str)
            if "KHz" in str:
                #print (str)
                freq_acq.append(float(str.strip("KHz\n"))) #da verificare
            else:
                line_int.append(int(str))
        freq_med = sum(freq_acq)/len(freq_acq)
        print ("frequenza media di acquisizione: %fkHz"%freq_med)
        print ("chiusura seriale")
        ard.close()
        return line_int
    except Exception as ex:
        print (ex)
        print ("errore - chiusura seriale")
        ard.close()
        return 1

def set_triangular_parameters(shp,amp,frq):
    bytes_to_send,clk_per_cnt = generate_bytes(clock_period,shp,amp,frq)
    try:
        usbToSer = serial.Serial(find_port("FTDI"),BAUDRATE,timeout=5)
        time.sleep(0.1)
        usbToSer.write(bytes_to_send[0])
        time.sleep(0.1)
        usbToSer.write(bytes_to_send[1])
        time.sleep(0.1)
        usbToSer.write(bytes_to_send[1])
        time.sleep(0.5)
        usbToSer.close()
        print ("impostata onda triangolare di frequenza %s"%frq)
    except Exception as ex:
        print (ex)
        usbToSer.close()
        print ("errore - chiusura seriale")
    return clk_per_cnt

def main():
    for frequency in freq_list:
        for presc in prescaler_list:
            print ("")
            print ("%sHz, presc: %s"%(frequency,presc))
            data_file = 'dati_seriale-f%s-p%s.txt'%(frequency,presc)
            graph_file = 'plot-f%s-p%s.png'%(frequency,presc)
            print (data_file)
            clk_cnt = set_triangular_parameters(shap,ampl_scelta,frequency)
            line_read_int = 1
            while(line_read_int == 1):
                line_read_int = arduino_sampling(presc)    
            if line_read_int != 1:
                print ("salvati %s punti"%num_points_acq)
                plot_graph(line_read_int,500,graph_file)
                with open(data_file, 'w') as f:
                    for lin in line_read_int:
                        line_str = "%s\n"%lin
                        f.write(line_str)
            else:
                print ("errore nel campionamento")
    return

if __name__ == "__main__":
    print(datetime.datetime.now().time())
    main()
    print(datetime.datetime.now().time())
    sys.exit(0)