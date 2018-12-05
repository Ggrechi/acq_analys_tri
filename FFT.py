import matplotlib.pyplot as plt
import numpy as np
from sys import exit
import scipy.fftpack

data_fil = 'dati_seriale-40HzTEST.txt'
#samp_freq = 19220
clock_period = (1/66.6)*1E-6 #in secondi

num_samples_arduino = 3500

#cerca nella lista wave_list il valore value e restituisce una lista 
#i cui elementi sono gli indici nei quali sono stati trovati
def search_code(wave_list,value):
    x_points = []
    for i, data in enumerate(wave_list):
        if data == value:
            x_points.append(i)
    return x_points

#legge il file e resituisce una lista di interi
def read_data_file(data_file):
    with open(data_file,'r') as f:
        data_list_int = [int(x) for x in f.readlines()]
    return data_list_int

#cerca lo all'interno della lista data_list_int, nell'intervallo definito da codes
#codes = [x1,x2] Quando sono presenti piu' zeri consecutivi, viene considerato solo 
#l'ultimo trovato. Restituisce una lista che contiene gli indici nei quali sono stati
#trovati.
def find_zero(codes,data_list_int):
    zeros = []
    for i in range(codes[0],codes[1]):
        if data_list_int[i] == 0:
            #print ("trovato uno zero!")
            zeros.append(i)
    indx = 0 #rimuove i punti consecutivi
    while indx < len(zeros)-1:
        if zeros[indx] == zeros[indx+1] - 1:
            del zeros[indx]
        else:
            indx = indx+1
    return zeros

#dati una lista di interi che contiene l'onda, la frequenza di campionamento
#disegna nel subplot num_subplot la trasformata di fourier del segnale
#ritorna null
def plotFFT(data_list_int, samp_freq, num_subplot):
    plt.subplot(num_subplot)
    N = len(data_list_int)
    T = 1.0 / samp_freq
    x = range(len(data_list_int))
    y = data_list_int
    yf = scipy.fftpack.fft(y)
    xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
    plt.yscale('log')
    plt.grid(True)
    yfft = 2.0/N * np.abs(yf[:N//2])
    list_yfft = [x for x in yfft]
    fft_mx_index = list_yfft.index(max(yfft[1:]))
    plt.plot(xf, yfft)
    plt.axvline(x=xf[fft_mx_index],color='r')
    print ("frequenza fondamentale FT: %f"%(xf[fft_mx_index]))
    #print (yfft[10:])
    return

def codes_search_difference(data_list_int,min_srch,max_srch):
    diff = []
    codice = []
    maxmin_code = []
    for d in range(min_srch,max_srch):
        x_values_found = search_code(data_list_int,d)
        #print (x_values_found)
        if len(x_values_found) > 1:
            x1 = x_values_found[0]
            i = 1
            x2 = x_values_found[-i]
            sign1 = data_list_int[x1-5] - data_list_int[x1]
            sign2 = data_list_int[x2-5] - data_list_int[x2]
            sign1 = sign1/abs(sign1)
            sign2 = sign2/abs(sign2)
            while sign1 != sign2:
                i = i + 1
                x2 = x_values_found[-i]
                sign1 = data_list_int[x1-5] - data_list_int[x1]
                sign2 = data_list_int[x2-5] - data_list_int[x2]
                sign1 = sign1/abs(sign1)
                sign2 = sign2/abs(sign2)
            codes = [x1,x2]
            difference = x2 - x1
            maxmin_code.append(codes)
            codice.append(d)
            diff.append(difference)
    return maxmin_code, codice, diff

def plot_wave(data_list_int,zero_list,codes,num_subplot):
    plt.subplot(num_subplot)
    t = range(len(data_list_int))
    plt.plot(t, data_list_int)
    if len(zero_list) > 1:
        for xvalue_zero in zero_list:
            plt.axvline(x=xvalue_zero,color='g')
        plt.axvline(x=codes[0],color='r')
        plt.axvline(x=codes[1],color='r')
    return

def sampl_freq(data_file_to_read, num_samples_ar,count_period_clk_counts):
    period_wave = count_period_clk_counts * clock_period * 4095 * 2
    data_list_int_all = read_data_file(data_file_to_read)
    data_list_int = data_list_int_all[:num_samples_ar]
    maxmin_code, codice, diff = codes_search_difference(data_list_int,5,1015)
    diff_max = max(diff)
    dif_mx_index = diff.index(max(diff))
    codes = maxmin_code[dif_mx_index]
    #print (diff_max)
    zero_list = find_zero(codes,data_list_int)
    #print (len(zero_list))
    samp_freq = max(diff)/(len(zero_list)*period_wave)
    print ("frequenza campionamento misurata: %fkHz"%(samp_freq/1000))
    #exit()
    plot_wave(data_list_int,zero_list,maxmin_code[dif_mx_index],211)
    plotFFT(data_list_int, samp_freq, 212)
    plt.show()

def main(count_period_clk_counts):
    sampl_freq(data_fil,num_samples_arduino,count_period_clk_counts)

if __name__ == "__main__":
    clk_cnt = 203 #16 per 500hz 203 per 40hz
    main(clk_cnt)