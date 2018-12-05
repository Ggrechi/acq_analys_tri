import sys

clock_period = (1/66.6)*1E-6 #in secondi

#shap_scelta = input("1:off\n2:triangolare\n3:costante\n4:quadra\n")
#if shap_scelta == '1':
#    shap = '00'
#    print ("off  %s"%shap)
#elif shap_scelta == '2':
#    shap = '11'
#    print ("triangolare  %s"%shap)
#elif shap_scelta == '3':
#    shap = '01'
#    print ("costante  %s"%shap)
#elif shap_scelta == '4':
#    shap = '10'
#    print ("quadra  %s"%shap)
#else:
#    print ("scelta errata")
#    sys.exit(0)

shap = '11'


#ampl_scelta = int(input("Ampiezza massima onda (0-7): "))
ampl_scelta = 3
bin_ampl_scelta = format(ampl_scelta, '03b')
byte1 = '0b00%s0%s'%(shap,bin_ampl_scelta)
#print (byte1)
byte1_int = int(byte1,2)
#print (byte1_int)
#print (byte1_char)
freq_list = [2,10,20,50,80,100,150,200,400,600,1500,2500,5000,8000]
#for frequency in freq_list:
frequency = float(input("frequenza onda (2 - 8000 Hz): "))
if True:
    periodo_sec = 1.0/frequency
    periodo_clk_counts = periodo_sec/clock_period
    clock_per_count = int(periodo_clk_counts/(2*4095))
    #periodo_scelta = int(input("periodo onda(1 - 4095): "))
    periodo_scelta = clock_per_count
    byte3_int = periodo_scelta >> 6
    byte2_int = periodo_scelta - (byte3_int << 6)
    #print (format(byte2, '06b'))
    #print (format(byte3, '06b'))
    periodo = clock_period*clock_per_count*1E3*4095.0*2.0 #in ms
    print ("colpi clock ad ogni incremento: %s"%clock_per_count)
    print ("periodo: %f ms"%periodo)
    print ("frequenza: %f kHz"%(1/periodo))
    print ("byte1: %s"%byte1_int)
    print ("byte2: %s"%byte2_int)
    print ("byte3: %s"%byte3_int)

    byte1_char = chr(byte1_int)
    byte2_char = chr(byte2_int)
    byte3_char = chr(byte3_int)