/*
NUM_SAMPLES e' il numero di campioni consecutivi acquisiti dall'ADC. E' limitato
dalla quantita' di memoria flash a disposizione; raggiunto il numero preimpostato
(campionando una volta ogni 13 colpi di clock ADC), la conversione si arresta,
i dati vengono inviati via seriale e poi ricomincia. La trasmissione seriale dei 
dati impiega molto piu' del tempo necessario per campionarli.
PRE_SCALER e' il coefficiente di divisione del clock di sistema (16MHz) per formare
il clock ADC. Il datasheet richiede una frequenza tra 50 e 200 KHz per avere 
piena risoluzione (frequenza dell'ADC clock). In realta' poi dice anche che fino
ad 1MHz non si ha perdita di risoluzione rilevante. I valori possibili per il 
prescaler sono 2 4 8 16 32 64 128 (implementati qui da 8 a 128).
*/
#define NUM_SAMPLES 3500
//#define PRE_SCALER 64
int PRE_SCALER;
volatile int numSamples=0;
int i = 0;
long t, t0; // t_serial, t0_serial;
volatile short values[NUM_SAMPLES];
//unsigned long times[NUM_SAMPLES];
void setup(){
    pinMode(13,OUTPUT);
    digitalWrite(13,0);
    Serial.begin(57600);
    while(Serial.available() == 0){}
    while (Serial.available() > 0) {
        PRE_SCALER = Serial.parseInt();
        if (Serial.read() == '#') {
            if(PRE_SCALER == 128 or PRE_SCALER == 64 or PRE_SCALER == 32
                                 or PRE_SCALER == 16 or PRE_SCALER == 8){
                digitalWrite(13,1);
            }
        }
    }
    DIDR0  |= 0xFF; //disattiva input digitali sui pin analogici
    DIDR2  |= 0xFF; //solo per atmega2560
    ADCSRA = 0;             // clear registro ADCSRA 
    ADCSRB = 0;             // clear registro ADCSRB 
    ADMUX |= (0 & 0x07);    // imposta tutti 0 nel registro ADMUX
    /////////////////// CAMBIARE SECONDO NECESSITA'!!!!
    ADMUX |= (1 << REFS0);  // impostazione reference voltage alimentazione
    //ADMUX |= (1 << REFS1);  // impostazione reference voltage interna 1.1v
    //ADMUX |= (1 << ADLAR);  // allinea a sinistra il valore letto per l'adc 8 bits from ADCH register
    //il sampling rate e' [ADC clock] / [prescaler] / [conversion clock cycles]
    //il clock e' 16 MHz e una conversione richiede 13 colpi di clock
    switch(PRE_SCALER){
        case 128:
            ADCSRA |= (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // 128 prescaler per 9.61 KHz
            break;
        case 64:
            ADCSRA |= (1 << ADPS2) | (1 << ADPS1);    // 64 prescaler per 19.2 KHz    
            break;
        case 32:
            ADCSRA |= (1 << ADPS2) | (1 << ADPS0);    // 32 prescaler per 38.5 KHz
            break;
        case 16:
            ADCSRA |= (1 << ADPS2);                     // 16 prescaler per 76.923 KHz teorici
            break;
        case 8:
            ADCSRA |= (1 << ADPS1) | (1 << ADPS0);    // 8 prescaler per 153.8 KHz
            break;
    }

    ADCSRA |= (1 << ADATE); // enable auto trigger
    ADCSRA |= (1 << ADIE);  // enable interrupts a conversione ADC completata
    ADCSRA |= (1 << ADEN);  // enable ADC
    ADCSRB |= (0 & 0x07); // free running mode, trigger automatico al completamento della conversione
    delay(1000);
    ADCSRA |= (1 << ADSC);  // start ADC
    t0 = micros();
}

ISR(ADC_vect){
    volatile short y = ADCL;  // legge 8 bit dall' ADC meno significativi
    volatile short x = ADCH;  // legge 8 bit dall' ADC più significativi
    y |= x << 8;
    //times[numSamples] = micros();
    values[numSamples] = y;
    numSamples++;
}

void loop(){
    
    if (numSamples>NUM_SAMPLES){
        //t0_serial = micros();
        t = micros()-t0;  // tempo trascorso
        ADCSRA &= ~(1 << ADATE); // disable auto trigger
        ADCSRA &= ~(1 << ADIE);  // disable interrupts a conversione ADC completata
        ADCSRA &= ~(1 << ADSC);  // stop ADC
        for (int j=0;j<NUM_SAMPLES;j++){
            //Serial.print(times[j]);
            //Serial.print(" ");
            Serial.println(values[j]);
            //Serial.println(j);
        }
        Serial.print((float)1000*NUM_SAMPLES/t);
        Serial.println("KHz");
        //i = i + 1;
        /*
        Serial.print("Frequenza di campionamento: ");

        */
        //Serial.println();
        /*
        int samples = NUM_SAMPLES;
        Serial.print("Durata acquisizione di 100 campioni: ");
        Serial.print(t);
        Serial.println(" us");
        t_serial = micros()-t0_serial;
        Serial.print("tempo utilizzo seriale: ");
        Serial.print(t_serial);
        Serial.println(" us");
        while(Serial.available() == 0){}
        Serial.read();
        */
        // restart
        ADCSRA |= (1 << ADATE); // enable auto trigger
        ADCSRA |= (1 << ADIE);  // enable interrupts a conversione ADC completata
        ADCSRA |= (1 << ADSC);  // start ADC
        t0 = micros();
        numSamples=0;
    }

}