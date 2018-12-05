import serial
import sys
import time
import glob
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt

read_or_mes = int(input("1: lettura file\n2: acquisizione file\n"))

if read_or_mes == 2:
    freq_or_nl = int(input("1: misura frequenza\n2: misura DNL e INL\n"))
    param = input("parametri misura: ")
    data_file = 'dati_seriale-%s.txt'%param

data_file_read = 'dati_seriale-500HzTEST.txt'
num_samples_arduino = 3500
bits_ADC = 10
INL0 = 0 #parametro da ben definire!
V_range = 5000.0 #in mV

def find_port(maker_str):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if maker_str in p.manufacturer:
            port = p.device
    return port

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
    
def plot_graph(int_list,code_to_search):
    fig, axes = plt.subplots(2, 2)
    bins_list = list(range(1,1024))
    for i,x in enumerate(bins_list):
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
    #print "numero di campionamenti tra il primo e l'ultimo codice %s trovati = %s"%(
    #                                                            code_to_search,num_max_camp)
    #for i,code in enumerate(codes):
    #    axes[0][0].axvline(x=code)
    #    if i>0:
    #        num_camp = code - codes[i-1]
    #        print ("numero di campionamenti tra due codici %s successivi: %s"%(code_to_search,num_camp))
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
    plt.show()

def search_code(wave_list,value):
    x_points = []
    last_index = 0
    for i, data in enumerate(wave_list):
        if data == value:
            x_points.append(i)
            last_index = i
    return x_points

def main():
    if read_or_mes == 2:
        if freq_or_nl == 2:
            num_points_acq = int(input("numero di punti da acquisire: "))
        else:
            num_points_acq = num_samples_arduino
        #print (num_points_acq)
        #sys.exit(0)
        
        ard = serial.Serial(find_port("Arduino"),57600,timeout=5)
        time.sleep(0.2)
        print ("scelta prescaler (8 16 32 64 128): ")
        prescaler = int(input())
        toSend = "%s#"%prescaler #il programma arduino richiede # come carattere finale
        try:
            ard.write(toSend)
            line_int = []
            print ("acquisizione %s punti"%num_points_acq)
            ard.reset_input_buffer()
            ard.reset_output_buffer()
            for index in range(num_points_acq):
                str = ard.readline().strip()
                if "KHz" in str:
                    print (str)
                else:
                    line_int.append(int(str))
            print ("chiusura seriale")
            ard.close()

            with open(data_file, 'w') as f:
                for lin in line_int:
                    line_str = "%s\n"%lin
                    f.write(line_str)
            print ("salvati %s punti"%num_points_acq)
            plot_graph(line_int,500)
        except Exception as ex:
            print (ex)
            print ("chiusura seriale")
            ard.close()
        sys.exit(0)

    elif read_or_mes == 1:
        lines = read_data_file(data_file_read)
        plot_graph(lines,500)
        sys.exit(0)

if __name__ == "__main__":
    main()