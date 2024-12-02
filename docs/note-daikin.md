# Solarmon

Note sul monitoraggio della pompa di calore Daikin Altherma 3H HT.

## 20221208

I primi riferimenti sono dei repository di alcune implementazioni già esistenti:

* https://github.com/zanac/pyHPSU
* https://github.com/Spanni26/pyHPSU
* https://github.com/raomin/ESPAltherma

Sembra assodato che il protocollo CAN non sia documentato, non c'è nulla di ufficiale reperibile in rete.

## 20221209

Un collaboratore di Zanac spiega nel dettaglio come hanno proceduto. Hanno optato per una daugther board CAN/Ethernet (PiCAN2):

* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-prima-parte/
* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-seconda-parte/
* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-terza-parte/

I tre articoli sono l'estratto del thread:

* https://cercaenergia.forumcommunity.net/?t=58409485

Le prime due implementazioni (Zanac e Spanni26) sfruttano l'interfaccia CAN (connettore J13) nella doppia modalità Ethernet/CAN (con la daughter board) e seriale/OBD con un adattatore basato sull'integrato ELM327. Il terzo (raomin) sfrutta invece una connessione seriale (connettore X10A) che, a detta di Spanni26, è particolarmente inefficiente rispetto al CAN, richiedendo centinaia di millisecondi per la lettura di un singolo parametro.

## 20221210

Trovata una nuova implementazione che utilizza una connessione seriale proprietaria Daikin;

* https://github.com/Arnold-n/P1P2Serial (o https://github.com/budulinek/Daikin-P1P2---UDP-Gateway, README.md più chiaro)

La connessione al bus P1P2 elettricamente non è banale (Arnold-n suggerisce l'uso di optoisolatori) e per questa ragione immediatamente scartata.

## 20221211

Andrea ha in casa un convertitore seriale/OBD basato sull'ELM327: è un "FORD modified ELM327". Ottimo, sarà oggetto di una verifica di fattibilità quanto prima.

## 20221212

Giornata dedicata allo studio delle specifiche dell'ELM327.

## 20221213

I comandi di inizializzazione dell'ELM327 secondo i sorgenti di Spanni26 (più recenti rispetto a quelli di Zanac, ma di fatto quasi identici) risultano essere i seguenti:

    ATE0        (ignora il valore di ritorno)
    AT PP 2F ON (15 tentativi a distanza di 1 secondo)
    AT D        (commentato, 1 unico tentativo)
    AT SP C     (15 tentativi a distanza di 1 secondo)

I comandi inviati per l'interrogazione del parametro "water_pressure" sono invece:

    ATSH190              (resetta l'interfaccia in caso d'errore)
    31 00 1C 00 00 00 00

Le sequenze `190` e `31 00 1C 00 00 00 00` cambiano da parametro a parametro e sono ricavate da un file JSON che è evidentemente frutto di un reverse-engineering (cfr. file [commands_hpsu.json](https://github.com/Spanni26/pyHPSU/blob/master/etc/pyHPSU/commands_hpsu.json)).

Il codice verifica che il primo carattere della risposta all'ultimo comando corrisponda al primo del comando (`3`, in questo caso); se no la risposta diventa `KO`. Se il controllo è soddisfatto, la risposta è la stringa ricevuta dall'ELM327.

Qual'è la semantica dei comandi?

    ATE0                 Echo off
    AT PP 2F ON          Enable Prog Parameter "2F" -- Protocol C (USER2) CAN baud rate divisor
    AT D                 Set all to defaults
    AT SP C              Set protocol to "C" -- User2 CAN (11* bit ID, 50* kbaud)

    ATSH190              Set Header to "190"
    31 00 1C 00 00 00 00 Daikin command

## 20221214

Collegamenti elettrici connettore J13/presa OBD:

    CAN-H ...... pin 6
    CAN-L ...... pin 14
    CAN-GND .... pin 5
    CAN-VCC .... <non necessario>

L'interruttore HS-CAN/MS-CAN sul convertitore USB/OBD "Ford modified ELM327" va impostato su "HS-CAN".

HS-CAN è la linea CAN ad alta velocità (detta anche "high-speed CAN" o "CAN C"), quella che insiste sui pin 6/14 della presa OBD; la linea MS-CAN ("mid-speed CAN" o "CAN B") è invece presente sui pin 3/11.

FORD modified ELM327: occorre verificare che non necessiti della tensione veicolo di 12V per funzionare; sarebbe interessante in questo senso conoscere la tensione al pin CAN VCC del connettore J13 della scheda della pompa di calore.

La speranza ora è che la versione dell'integrato montato nell'adattatore supporti il comando PP (alcuni utenti hanno acquistato delle versioni dell'adattatore che non consentono di modificare l'impostazione del protocollo, in particolare non permettono la selezione del protocollo C - "User2 CAN").

## 20221218

Prima prova di comunicazione con l'adattatore da PC con putty a 500Kpbs (Andrea si ricorda che l'ultima volta che lo aveva utilizzato per analizzare la Focus aveva impostato questa velocità):

    AT PPS
    >C:81 N 2D:04 N 2E:80 F 2F:0A F

L'adattatore risponde; come reagisce alla sequenza di inizializzazione per la CAN Daikin?

    ATE0
    AT PP 2F ON
    AT SP C

Tutti i comandi hanno risposto OK! Passando a Termite, che conosco meglio, dopo averlo opportunamente configurato si legge:

    >ATE0
    OK

    >ATPPS
    00:FF F 01:FF F 02:FF F 03:32 F
    04:01 F 05:FF F 06:F1 F 07:09 F
    08:FF F 09:00 F 0A:0A F 0B:FF F
    0C:08 N 0D:0D F 0E:9A F 0F:FF F
    10:0D F 11:00 F 12:FF F 13:32 F
    14:FF F 15:0A F 16:FF F 17:92 F
    18:00 F 19:28 F 1A:FF F 1B:FF F
    1C:FF F 1D:FF F 1E:FF F 1F:FF F
    20:FF F 21:FF F 22:FF F 23:FF F
    24:00 F 25:00 F 26:00 F 27:FF F
    28:FF F 29:FF F 2A:38 N 2B:02 F
    2C:81 N 2D:04 N 2E:80 F 2F:0A N
    >ATE0
    OK

    >AT PP 2F ON
    OK

    >AT SP C
    OK

E' ora di cablare il lato OBD:

    cavo blu:          CAN-H ...... pin 6
    cavo marrone:      CAN-L ...... pin 14
    cavo giallo/verde: CAN-GND .... pin 5

Cosa accade se si invia la richiesta di lettura del parametro "water_pressure"?

    >ATSH190
    OK

    >31 00 1C 00 00 00 00
    CAN ERROR

Forse va inviata la sequenza binaria anziché quella esadecimale? Qualcosa in questo caso arriva (la sequenza è stata inviata attraverso il comando "Send File" dopo aver preparato un file con il contenuto binario equivalente), ma non è leggibile -- non è una stringa ASCCI, e la cosa tutto sommato è anche comprensibile; in ogni caso non è `CAN ERROR`, e questo fa ben sperare.

## 20221219

Linux assegna il dispositivo /dev/ttyUSB0 al primo dispositivo USB che viene connesso al PC; poiché ora ci saranno due dispositivi USB collegati alla Raspberry (adattatore USB/RS485 e USB/OBD) potrebbe accadere che a volte i due adattatori verranno montati in un certo ordine, altre volte in ordine inverso; sarebbe opportuno assegnare ad ognuno dei due adattatori un nome fisso e univoco.

Non è difficile farlo, è sufficiente ricavare `idVendor` e `idProduct` dei due adattatori e usare queste informazioni per fare in modo che il sistema operativo associ loro un nome simbolico univoco. I due attributi sono ricavabili attraverso il comando `lsusb` e/o `dmesg` e/o `udevadm` (da lanciare dopo aver collegato i due dispositivi), dopodiché si procede alla creazione del file `/etc/udev/rules.d/10-usb-serial.rules`:

    sudo nano /etc/udev/rules.d/10-usb-serial.rules

Il file contiene le istruzioni per creare un link simbolico per ognuno dei due dispositivi:

    SUBSYSTEM=="tty", ATTRS{idProduct}=="....", ATTRS{idVendor}=="....", SYMLINK+="ttyUSB_MYDEV1"
    SUBSYSTEM=="tty", ATTRS{idProduct}=="....", ATTRS{idVendor}=="....", SYMLINK+="ttyUSB_MYDEV2"

Per rendere effettiva la nuova configurazione dare il comando:

    sudo udevadm trigger

Verificare che i link simbolici appaiono automaticamente quando si aggiunge un dispositivo, così come all'avvio, se i dispositivi sono già collegati prima dell'accensione della Raspberry Pi.

Per distinguere due dispositivi con identici `idVendor` e `idProduct` è necessario individuare un terzo attributo discriminante e modificare conseguentemente il file `.rules`; fortunatamente non è questo il caso:

    SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyUSB_RS485"
    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="ttyUSB_HSCAN"

L'effetto è quello desiderato:

    pi@emonpi:/ $ ls -al /dev/ttyUSB*
    crw-rw---- 1 root dialout 188, 0 Dec 20 21:54 /dev/ttyUSB0
    crw-rw---- 1 root dialout 188, 1 Dec 20 21:53 /dev/ttyUSB1
    lrwxrwxrwx 1 root root         7 Dec 20 21:53 /dev/ttyUSB_HSCAN -> ttyUSB1
    lrwxrwxrwx 1 root root         7 Dec 20 21:53 /dev/ttyUSB_RS485 -> ttyUSB0

## 20221221

La comunicazione seriale PC/ELM327 è di tipo 8,N,1 con baudrate predefinito di 38400; l'integrato ELM327 supporta tuttavia 6 baudrate:

* 19.2
* 38.4
* 57.6
* 115.2
* 230.4
* 500

La velocità viene selezionata scrivendo l'apposito divisore nel registro `C0` con il comando:

    AT PP C0 SV xx

Per rendere effettiva la nuova velocità è necessario attivarla, quindi resettare l'integrato:

    AT PP C0 ON
    AT Z

La velocità del bus CAN per il protocollo C "User1 CAN" è regolata dal registro `2F`, che va impostato secondo le stesse modalità:

    AT PP 2F SV xx
    AT PP 2F ON
    AT Z

In questo caso il comando di reset può essere sostituito dal comando di "Warm start" che ha lo stesso effetto ma è più veloce (rispetto al reset completo il "Warm start" non effettua il test dei LED, che richiede circa 1 secondo per essere completato):

    AT PP 2F SV xx
    AT PP 2F ON
    AT WS

## 20221222

L'adattatore seriale/OBD in questo momento è configurato per una CAN a 50Kbps; il parametro programmabile `2F`, che risulta attivo (cfr. `N` accanto al parametro), è infatti valorizzato a `0A`:

    >ATPPS
    00:FF F 01:FF F 02:FF F 03:32 F
    04:01 F 05:FF F 06:F1 F 07:09 F
    08:FF F 09:00 F 0A:0A F 0B:FF F
    0C:08 N 0D:0D F 0E:9A F 0F:FF F
    10:0D F 11:00 F 12:FF F 13:32 F
    14:FF F 15:0A F 16:FF F 17:92 F
    18:00 F 19:28 F 1A:FF F 1B:FF F
    1C:FF F 1D:FF F 1E:FF F 1F:FF F
    20:FF F 21:FF F 22:FF F 23:FF F
    24:00 F 25:00 F 26:00 F 27:FF F
    28:FF F 29:FF F 2A:38 N 2B:02 F
    2C:81 N 2D:04 N 2E:80 F 2F:0A N

Nè i sorgenti di Zanac né quelli di Spanni26 si preoccupano di impostare questo parametro, forse perché fatto una volta per tutte all'inizio (tutti i parametri programmabili sono persistenti e il loro valore non viene perso nemmeno dopo uno spegnimento). Forse la ragione per cui le sequenze esadecimali non sono state riconosciute durante il primo test dipende dall'errata impostazione della velocità del bus e non dal fatto che l'ELM327 si aspetta delle sequenze binarie pure.

## 20221224

Di seguito l'esito di una sessione di monitoraggio con le impostazioni attuali:

    >AT H1
    OK

    >AT D1
    OK

    >AT MA
    000 0 RTR <RX ERROR
    000 0 RTR
    078 0 RTR <RX ERROR
    078 0 RTR
    078 0 RTR <RX ERROR
    STOPPED

Effettivamente c'è qualcosa che non va. Portando la velocità del bus CAN a 20Kbps la situazione cambia:

    >AT PP 2F SV 19
    OK

    >AT PP 2F ON
    OK

    >AT WS
    >LM327 v1.4

    >AT PPS
    ... 2F:19 N

    >AT MA
    31 00 FA 06 95 00 00
    22 0A FA 06 95 00 00
    61 00 FA 01 1A 00 00
    22 0A FA 01 1A 00 00
    61 00 FA 13 58 00 00
    22 0A FA 13 58 00 00
    STOPPED.

Funziona! E le interrogazioni? Che risposta si ottiene alla richiesta della temperatura esterna?

    >ATSH310
    OK

    >61 00 FA 0A 0C 00 00
    22 0A FA 01 1A 00 00
    22 0A FA 13 58 00 00
    22 0A FA 01 EC 00 00
    22 0A FA 01 1E 00 00
    22 0A FA 13 53 00 00
    22 0A FA 0A 0C 00 74 -> 11.6°

    >61 00 FA 0A 0C 00 00
    NO DATA

    >61 00 FA 0A 0C 00 00
    NO DATA

Mhm, strano. Cosa succede se si richiede il valore di pressione dell'acqua?

    >ATSH190
    OK

    >31 00 1C 00 00 00 00
    NO DATA

    >31 00 1C 00 00 00 00
    22 0A 0C 00 6F 00 00 -> 111

    >31 00 1C 00 00 00 00
    22 0A 0C 00 6F 00 00 -> 111

    >31 00 1C 00 00 00 00
    22 0A 0C 00 70 00 00 -> 112

    >31 00 1C 00 00 00 00
    NO DATA

`NO DATA` è la risposta dell'ELM327 quando scade il timeout di lettura, che di default è pari a 205ms.

Il timeout è controllato dal parametro programmabile `03` a passi di 4.096ms; per esempio, per impostare il timeout a 400ms è sufficiente impostare il parametro a `64` (100 decimale). Anche innalzandolo al massimo (`FF`, corrispondente a poco più di 1 secondo), e disattivando il controllo adattativo dei timeout la situazione non migliora, nella maggior parte dei casi la risposta che si ottiene è `NO DATA` oppure dei pacchetti non correlati al parametro richiesto.

I `NO DATA` non dovrebbero dipendere da problemi relativi agli identificativi dei parametri: per quando Zanac e Spanni26 utilizzino un modello diverso di pompa di calore, i pacchetti acquisiti per la Altherma differiscono da quelli riportati nelle analisi di Zanac solamente per i valori assunti dai parametri, ma gli identificativi corrispondono perfettamente, anche quelli dei nodi della rete.

Come controprova, il codice di Spanni26 soffre dello stesso problema con questa pompa di calore:

    pi@emonpi:~/pyHPSU $ python3 pyHPSU.py -d ELM327 -p /dev/ttyUSB1 -c t_hs
    warning - sending cmd 31 00 FA 01 D6 00 00 (rc:NO DATA)
    warning - retry 1 command t_hs
    warning - sending cmd 31 00 FA 01 D6 00 00 (rc:NO DATA)
    warning - retry 2 command t_hs
    warning - sending cmd 31 00 FA 01 D6 00 00 (rc:NO DATA)

Nemmeno la velocità di comunucazione del canale seriale ha effetto sui `NO DATA`.

Che sia una questione di priorità? Nel datasheet dell'ELM327 si legge:

> You may find that some requests, being of a low
> priority, may not be answered immediately, possibly
> causing a 'NO DATA' result. In these cases, you may
> want to adjust the timeout value, perhaps first trying
> the maximum (ie use AT ST FF). Many vehicles will
> simply not support these extra addressing modes.

## 20221226

Sto cominciando a pensare che il problema potrebbe essere imputabile all'ELM327. Quello a disposizione ha versione 1.4, sufficiente per consentire il cambio di protocollo, ma nel forum cercaenergia si consiglia la versione 2.0 o superiore. Un collega ne ha un paio da potermi prestare, nel frattempo mi chiedo se uno "sniffing" passivo possa fornire tutti i dati che interessano ad Andrea. Del resto per il momento non c'è interesse a modificare i parametri di funzionamento della pompa.

Statistiche raccolte dopo un paio d'ore di monitoraggio del bus CAN:

* eventi registrati: 1163
* errori: 210 -- quasi sicuramente imputabili al codice
* pacchetti `t_ext`: 717
* pacchetti `sw_vers_01`: 34
* pacchetti `mode_01`: 34
* pacchetti `water_pressure`: 34
* pacchetti `t_hc_set`: 34
* pacchetti `t_hs`: 33
* pacchetti `t_dhw`: 33

La temperatura esterna (`t_ext`) transita ogni 10s; gli altri parametri si presentano con un pattern regolare quanto inaspettato: due letture a distanza di un minuto intervallate da un intervallo di silenzio di sei minuti. Questi sono i primi rilievi registrati:

    15:12:01
    15:13:10
    15:19:02
    15:20:10
    15:26:02
    15:27:10
    15:33:01
    15:34:10
    15:40:02
    15:41:14
    ...

----

Grazie al comando `PB` risulta più comodo utilizzare il protocollo B rispetto al C; la configurazione, per quanto non persistente, è infatti più immediata:

    AT PB 80 19
    AT SP B

Il cambio di protocollo non produce effetti collaterali sullo sniffing, al momento viene promosso a soluzione preferita (il valore `80` è stato scelto perché è il default per il protocollo C, cfr. parametro programmabile `2E`).

----

Il comando `ATBD` mostra il contenuto del buffer di trasmissione/ricezione. Invocando questo comando subito dopo la ricezione di un pacchetto, nel buffer sembra ci siano sempre 11 byte:

    >ATMA
    180 7 22 0A 0C 00 6C 00 00
    STOPPED
    >ATBD
    0B 00 00 01 80 22 0A 0C 00 6C 00 00 00

Lo stesso comando lanciato dopo aver ricevuto un `NO DATA` in risposta ad una interrogazione, ne riporta 12:

    >ATSH190
    OK
    >31 00 1C 00 00 00 00
    NO DATA
    >ATBD
    0C 00 00 01 90 31 00 1C 00 00 00 00 00

Una discrepanza inattesa, per simmetria me ne sarei aspettati 11.

Dopo un comando `ATAL` "Allow long messages" (con lunghezza superiore a 7 bytes) o `ATNL` -- "Normal length messages" `ATMA` mostra sempre un `DLC` di 7 byte; le interrogazioni ritornano `NO DATA` indipendentemente dall'impostazione `AL`/`NL` attiva.

## 20221228

Approntato una versione dello sniffer con un thread di polling che pubblica i valori dei parametri raccolti.

## 20221229

Rifattorizzato il codice suddividendolo nelle componenti elm327.py, daikin_altherma.py e daikin_altherma_sniffer.py.

## 20221231

Esistono alternative all'interrogazione via seriale dell'ELM327?

* https://python-obd.readthedocs.io/en/latest/ - no, supporta solo protocolli automotive:

        [https://github.com/brendan-w/python-OBD/blob/master/obd/elm327.py]
        ...
        _SUPPORTED_PROTOCOLS = {
            # "0" : None,
            # Automatic Mode. This isn't an actual protocol. If the
            # ELM reports this, then we don't have enough
            # information. see auto_protocol()
            "1": SAE_J1850_PWM,
            "2": SAE_J1850_VPW,
            "3": ISO_9141_2,
            "4": ISO_14230_4_5baud,
            "5": ISO_14230_4_fast,
            "6": ISO_15765_4_11bit_500k,
            "7": ISO_15765_4_29bit_500k,
            "8": ISO_15765_4_11bit_250k,
            "9": ISO_15765_4_29bit_250k,
            "A": SAE_J1939,
            # "B" : None, # user defined 1
            # "C" : None, # user defined 2
        }
        ...

    [Qui](https://stackoverflow.com/questions/57134822/python-obd-most-commands-not-supported) si vede che la libreria usa i soliti comandi `AT`.

* https://python-can.readthedocs.io/en/stable/ - questa è una libreria generica, ma non è chiaro se supporta l'ELM327.

## 20230101

Reperito in rete ulteriori informazioni sul protocollo Daikin:

* https://github.com/crycode-de/ioBroker.canbus/blob/master/well-known-messages/configs/rotex-hpsu.md
* https://forum.iobroker.net/topic/52171/rotex-hpsu-daikin-altherma-w%C3%A4rmepumpe-%C3%BCber-iobroker-canbus (in tedesco)

* https://github.com/ahermann86/fhemHPSU

Quest'ultima, realizzata in Perl, invia un comando aggiuntivo durante l'inizializzazione, un `ATV1` -- "Variable data lengths off or on". Questo comando disabilita lo *stuffing* e di fatto permette finalmente di ricevere le risposte alle richieste inviate:

    >ATSH190
    OK
    >31 00 1C 00 00 00 00
    32 10 1C 04 DA 00 00
    >
    32 10 1C 04 DA 00 00
    >
    32 10 1C 04 DA 00 00

    >ATSH310
    OK
    >61 00 FA 0A 0C 00 00
    22 0A 0C 00 64 00 00
    62 10 FA 0A 0C 00 64
    >
    62 10 FA 0A 0C 00 64
    >
    62 10 FA 0A 0C 00 64

Dopo alcune prove sembra assodato che il problema fosse proprio riconducibile allo *stuffing* effettuato dall'ELM327. Le soluzioni possibili sono 2: inviare il comando `ATV1` in fase di inizializzazione oppure porre a 1 il bit 6 della maschera di configurazione del protocollo `B` con il comando `ATPBE019`. Questo bit controlla la lunghezza del pacchetto immesso nel bus CAN da parte dell'ELM327: se posto a 0 l'integrato aggiunge tanti byte nulli quanti servono a raggiungere gli 8 byte, se posto a 1 invia esattamente il numero di byte specificati.

Approntato in fretta e furia uno script che interroga la pompa di calore chiamando in causa parametri che lo sniffing non ha mai rilevato:

    pi@emonpi:~/daikin python3 daikin_altherma_monitor.py
    date,t_dhw,water_pressure,mode_01,t_hs,t_ext,t_return,flow_rate,t_hc,duration
    2023-01-01 23:16:02.817596,48.0,1.252,3,31.4,10.8,29.0,0,40.8,0:00:01.887648
    2023-01-01 23:16:13.983256,48.0,1.253,3,31.3,10.8,29.0,0,40.4,0:00:01.159685
    2023-01-01 23:16:25.117180,48.0,1.254,3,31.3,10.8,29.0,0,40.1,0:00:01.123707
    2023-01-01 23:16:36.122904,48.0,1.254,3,31.3,10.8,29.0,0,40.6,0:00:00.997076
    2023-01-01 23:16:47.080784,48.0,1.254,3,31.3,10.8,29.0,0,40.7,0:00:00.947647
    2023-01-01 23:16:58.054747,48.0,1.254,3,31.3,10.8,29.0,0,40.4,0:00:00.963630
    2023-01-01 23:17:09.028629,48.0,1.254,3,31.3,10.8,29.0,0,40.6,0:00:00.963777
    2023-01-01 23:17:20.002484,48.0,1.252,3,31.3,10.8,29.0,0,40.6,0:00:00.963557
    2023-01-01 23:17:30.960356,48.0,1.252,3,31.3,10.8,29.0,0,40.6,0:00:00.947596
    2023-01-01 23:17:41.934268,48.0,1.254,3,31.3,10.8,29.0,0,40.4,0:00:00.965767
    ...

Lo script impiega circa 1 secondo per leggerli; aumentando il numero di parametri a 20, il tempo richiesto sale a poco meno di 4 secondi.

Idea: per ridurre il traffico seriale verso l'ELM327 conviene raggruppare i parametri per identificativo del nodo di destinazione in modo da minimizzare il numero di comandi `ATSH` necessari.

## 20220102

Seguono un paio di considerazioni di Zanac circa la frequenza di campionamento:

> p.s. ho già fatto esperimenti di bombing, le richieste prioritarie non intasano il bus, e l'hpsu continuava a lavorare e mandare dati sul display! Con 37 richieste ogni 2 minuti siamo centinaia di volte sotto il bombing che ho testato.

Fonte: https://cercaenergia.forumcommunity.net/?t=58409485&st=165#entry421712957

> 20000 baud / 108 bit per messaggio di richiesta = 185 richieste AL SECONDO...
> Dimezziamole per includere anche le risposte, più di 90 richieste / risposte AL SECONDO!!!!

Fonte: https://cercaenergia.forumcommunity.net/?t=58409485&st=165#entry421713021

Del resto nello stesso forum si legge anche, sempre da Zanac:

>Se la scatola che contiene l'elm327 ha la scritta "v1.5a" evitatela... cercate di comprare una con "v 2.1". I cloni con versione 2.1 a quanto sembra implementano tutte le specifiche elm327!

Fonte: https://cercaenergia.forumcommunity.net/?t=58409485&st=75#entry421644594

In questo caso con una 1.4 noi ce l'abbiamo fatta!

----

Prima prova di campionamento di 40 parametri con periodo di 30 secondi su un arco temporale di poco più di due ore (cfr. file **docs/data/daikin/altherma_20230102160045.csv**)

* campionamenti effettuati: 203
* campionamenti parziali: 7 (~3%)
* tempo impiegato per raccogliere un campione: 9.5s (min 2.7s, max 10.8s)

Tutti i campionamenti parziali sono falliti a causa di un errore "invalid frame size (got 7, expected 14)".

----

Ridotto il numero di parametri campionati perché alcuni evidentemente cloni, altri momentaneamente mantenuti in attesa di approfondimenti.

Parametri eliminati:

* qchhp
* qsc
* ta2
* heat_slope
* t_dhw_setpoint1
* t_dhw_setpoint2
* t_dhw_setpoint3
* hyst_hp

Cloni:

* t_hs, t_v1: tenuto il primo
* t_ext, t_outdoor_ot1: tenuto il primo
* t_dhw, tdhw2, t_dhw1: tenuto il primo
* t_return, tr2, t_r1: tenuti tutti e tre
* t_hc, tvbh2, t_vbh: tenuti tutti e tre

Parametri non in elenco

Un parametro ritenuto interessante è "Energia elettrica totale" per il quale il display in questo istante mostra l'indicazione "3004 kWh". Sicuramente non c'è alcun parametro, tra i 40 acquisiti in questo momento, che assuma quel valore. Nell'elenco di Zanac o di Spanni26 che corrisponda a quell'etichetta. Considerando che 3004d corrisponde a 0BBCh, ricorriamo al monitor dell'ELM327:

    ...
    >ATPBC019
    OK
    >ATSPB
    OK
    >ATH1
    OK
    >ATD1
    OK
    >ATMA
    10A 7 31 00 FA 06 95 00 00
    180 7 22 0A FA 06 95 00 00
    10A 7 61 00 FA 01 1A 00 00
    300 7 22 0A FA 01 1A 00 00
    10A 7 61 00 FA 13 58 00 00
    300 7 22 0A FA 13 58 00 00
    ...
    10A 7 31 00 FA C2 FA 00 00
    180 7 22 0A FA C2 FA 0B BC

Trovato! Il parametro è identificato dal codice `C2FA` ed effettivamente non compare nell'elenco delle implementazioni di riferimento. Conviene verificare che l'interrogazione funziona anche da terminale:

    >ATSH190
    OK
    >31 00 FA C2 FA 00 00
    180 7 22 0A FA 06 7E 00 50
    180 7 32 10 FA C2 FA 0B BC
    >

Il primo pacchetto della risposta non c'entra nulla, si tratta verosimilmente di uno di quelli che transitano di tanto in tanto nel bus. Il secondo pacchetto è la risposta attesa. Bene!

## 20220103

Effetto del ritardo sul numero di campioni persi/parziali:

* nessun ritardo (cfr. file **docs/data/daikin/altherma_20230102160045.csv**): 7 su 203 (3.4%)
* ritardo di 100ms tra un comando e il successivo (cfr. file **docs/data/daikin/altherma_20230102210718.csv**): 3 su 118 (2.5%)
* ritardo di 50ms tra invio del comando e attesa della risposta (cfr. file **docs/data/daikin/altherma_20230103010406.csv**): 5 su 238 (2.1%)

Una ripetizione senza ritardi extra (cfr. file **docs/data/daikin/altherma_20230103092947.csv**), sempre estesa su due ore, ha fornito esattamente gli stessi risultati dell'ultima prova, 5 campioni parziali su un totale di 238. Evidentemente il ritardo introdotto è coperto dal timeout della connessione seriale.

La natura degli errori che impediscono la corretta lettura dei parametri è sempre la stessa:

    2023-01-03T10:38:02 WARNING Error "wrong size for frame [b'NO DATA'] (got 7, expected 14)" while reading parameter "qch"...
    2023-01-03T10:38:02 WARNING Error "wrong size for frame [b'NO DATA'] (got 7, expected 14)" while reading parameter "qwp"...
    2023-01-03T10:38:02 WARNING Error "wrong size for frame [b'NO DATA'] (got 7, expected 14)" while reading parameter "qdhw"...
    2023-01-03T10:38:02 WARNING Error "wrong size for frame [b'NO DATA'] (got 7, expected 14)" while reading parameter "tvbh2"...
    2023-01-03T10:38:02 WARNING Error "wrong size for frame [b'NO DATA'] (got 7, expected 14)" while reading parameter "tliq2"...
    ...

In un certo senso è confortante, la procedura di lettura non perde pezzi per strada.

Ad ogni modo non emerge nessuno schema specifico nei campioni parziali; il primo `NO DATA` si verifica in corrispondenza di un parametro qualunque e allo stesso modo scompaiono. Il cambio di nodo non sembra influenzare il fenomeno:

    parameter        node    value
    t_hs             190        20.9
    t_hs_set         190        42
    water_pressure   190         1.17
    t_dhw            190        42.8
    t_dhw_set        190        48
    t_return         190        21
    flow_rate        190      1110
    status_pump      190         0
    runtime_comp     190      1702
    runtime_pump     190      2787
    posmix           190         0
    qboh             190   NO DATA
    qch              190   NO DATA
    qwp              190   NO DATA
    qdhw             190   NO DATA
    tvbh2            190   NO DATA
    tliq2            190   NO DATA
    tr2              190   NO DATA
    mode             190   NO DATA
    pump             190   NO DATA
    ehs              190   NO DATA
    bpv              190   NO DATA
    t_vbh            190   NO DATA
    t_r1             190   NO DATA
    v1               190   NO DATA
    total_energy     190   NO DATA
    t_ext            310   NO DATA
    t_hc_set         310        42
    t_hc             610        21.2

Lo schema sottostante riporta i parametri mancanti nei 5 campioni parziali raccolti nell'acquisizione **docs/data/daikin/altherma_20230103092947.csv**:

    +++++++++++----------------++
    -----++++++++++++++++++++++++
    ++++++++++++----------------+
    -++++++++++++++++++++++++++++
    +++++++++++++++++++----------

    +: dato presente
    -: NO DATA

## 20230104

Effettuata un'acquisizione di 8 ore senza pause extra, che ha confermato il tasso di campioni incompleti: 23 su 951, pari al 2.4% (cfr. file **docs/data/daikin/altherma_20230103114302.csv**).

----

Per determinare, tra i potenziali parametri "clone", quali sono visualizzati sul display della pompa di calore, sono state effettuate 5 catture, una per ogni pagina dell'interfaccia utente.

**ATTENZIONE**: una cattura potrebbe aver avuto inizio prima della visualizzazione della pagina relativa, potrebbe quindi contenere richieste legate ancora alla pagina precedente.

### Valori visualizzati

Pagina 1:

    3 Gen 2023
    20:11
    47.7°C (icona: doccia)
    28.0°C (icona: radiatore)
    1.3bar (icona: boiler)
    10.2°C (icona: tempo variabile)
    Altre icone:
        Ext,
        ??? (onde verticali),
        Unità esterna ON,
        Defrost ON

Pagina 2:

    T-AU: 9.4°C
    t-liq: 7.0°C
    P: 1.34bar
    t-R: 35.0°
    t-V: 33.4°C
    V: 1134l/h
    t-V,BH: 33.4°C
    t-DHW: 47.7°C

Pagina 3:

    B1: 12%
    DHW: 0%

Pagina 4:

    Temperatura mandata attuale: 30.6°C
    Temperatura mandata nom.: 42.0°C
    Temperatura esterna media: 10.2°C
    Temperatura ACS attuale: 47.7°C
    Temperatura ACS nom.: 48.0°C
    Temperatura ritorno: 35.5°C

Pagina 5:

    Temperatura mandata CR attuale: 36.2°C
    Temperatura mandata CR nom.: 42.0°C
    Temperatura di mandata PHX: 36.1°C
    Temperatura di mandata BUH: 36.2°C
    Temperatura esterna (opzione): N.A.
    Temperatura refrigerante: 29.5°C

### Analisi degli ultimi 100 pacchetti delle singole catture

Va tenuto presente che nel bus viaggiano "autonomamente" i seguenti parametri:

* t_dhw (0E)
* water_pressure (1C)
* mode_01 (0112)
* t_hs (01D6)
* t_ext (0A0C)

Nei prospetti sottostanti, REQ indica il codice del parametro richiesto dal display (header 10A), RESP quello del pacchetto di risposta, VALUES l'elenco dei valori (espressi in decimale) assunti dal parametro, SPANNI26 il nome assegnato al parametro dall'implementazione di Spanni26.

La REQ "----" indica che a quella risposta non corrisponde nessuna richiesta: potrebbe trattarsi di una risposta ad una richiesta che per qualche ragione non fa parte della cattura o più verosimilmente che si tratta di un pacchetto pubblicato spontaneamente da un nodo.

Pagina 1:

    REQ  RESP VALUES                    SPANNI26
    ==================================================
    1358 1358 0 0 0 0 0                 -
    ---- 0822 310 295                   -
      0C   0C 96 96 95 95 94            -
    1353 1353 0 0 0 0 0                 -
    C0B4 C0B4 34                        sw_vers_02
    0A0C 0A0C 102 102 102 102 102       t_ext
    0695 0695 0 0 0 0 0                 air_purge
    C0C4 C0C4 0 0 0 0 0                 -
    011A 011A 0 0 0 0 0                 screed
    01EC 01EC 0 0 0 0 0                 -
    ----   0D 310 295                   -
    011E 011E 0 0 0 0 0                 -
    ---- 01D6 278                       t_hs

Pagina 2:

    REQ  RESP VALUES                    SPANNI26
    ==================================================
    C0FC C0FC 356 358 359 360           t_v1
    C0FB C0FB 12 12 12 12               bpv
    C0FE C0FE 355 357 358 359           t_vbh
    069B 069B 0 0 0 0                   posmix
    FDAC FDAC 256 256 256 256           -
    C176 C176 94 94 94                  -
      61   61 0 0 0 0                   -
      1C   1C 1337 1336 1337 1338       water_pressure
    C0F9 C0F9 0 0 0 0                   ehs
    C104 C104 360 360 361 365           tr2
    C106 C106 477 477 477 477           tdhw2
    C101 C101 1134 1122 1140 1122       v1
    C103 C103 80 85 85 85               tliq2

Pagina 3:

    REQ  RESP VALUES                    SPANNI26
    ==================================================
    C0FC C0FC 356 356 355 355           t_v1
    C0FB C0FB 27 37 42 47               bpv
    C101 C101 0 0 366 1608              v1
    C0FE C0FE 357 356 356 356           t_vbh
    069B 069B 0 0 0 0                   posmix
    FDAC FDAC 0 0 0 256                 -
    C176 C176 93 93 93                  -
      61   61 256 256 256 256           -
      1C   1C 1348 1351 1330 1324       water_pressure
    ---- C15B 1                         -
    C104 C104 360 360 360 360           tr2
    C106 C106 477 477 477 477           tdhw2
    C0F9 C0F9 0 0 0 0                   ehs
    C103 C103 95 95 95 95               tliq2

Pagina 4:

    REQ  RESP VALUES                    SPANNI26
    ==================================================
    C0FC C0FC 412 394 376 365           t_v1
      02   02 420 420 420               t_hs_set
      04   04 420 420 420 420           t_hc_set
    C0FE C0FE 406 390 374 365           t_vbh
      03   03 480 480 480               t_dhw_set
    ---- 0822 379                       -
      16   16 350 350 350               t_return
    0A0C 0A0C 102 102 102               t_ext
    01DA 01DA 1926 1890 1902 1902       flow_rate
      1C   1C 1309 1312 1310 1311       water_pressure
      0F   0F 389 373 365               t_hc
      0D   0D 390 379 373 365           -
      0E   0E 477 477 477               t_dhw
    C105 C105 65136 65136 65136 65136   ta2
    ---- 01D6 385 370                   t_hs
    C103 C103 105 151 185 215           tliq2

Pagina 5:

    REQ  RESP VALUES                    SPANNI26
    ==================================================
    C0FC C0FC 393 395 396 396           t_v1
      02   02 420 420 420               t_hs_set
    C0B4 C0B4 34                        sw_vers_02
      04   04 420 420 420 420           t_hc_set
    C0FE C0FE 391 394 395 395           t_vbh
      03   03 480 480 480               t_dhw_set
    ---- 0822 394                       -
      16   16 340 340 340               t_return
    0A0C 0A0C 102 102 102               t_ext
    01DA 01DA 786 810 786 792           flow_rate
      1C   1C 1344 1344 1342 1344       water_pressure
      0F   0F 394 395 396               t_hc
      0D   0D 394 394 395 395           -
      0E   0E 477 477 477               t_dhw
    C105 C105 65136 65136 65136 65136   ta2
    C103 C103 350 355 355 360           tliq2

Una possibile, per quanto incompleta, associazione potrebbe essere:

    DISPLAY READING                           ID   SPANNI26       NOTE
    ==========================================================================
    3 Gen 2023................................????
    20:11.....................................????
    47.7°C (icona: doccia)....................  0E t_dhw          da sniffing?
    28.0°C (icona: radiatore).................01D6 t_hs           da sniffing?
    1.3bar (icona: boiler)....................  1C water_pressure da sniffing?
    10.2°C (icona: tempo variabile)...........0A0C t_ext          da sniffing?
    Altre icone:
        Ext...................................????
        ??? (onde verticali)..................????
        Unità esterna ON......................????
        Defrost ON............................????

    T-AU: 9.4°C...............................C176 <ASSENTE>
    t-liq: 7.0°C..............................C103 tliq2
    P: 1.34bar................................  1C water_pressure
    t-R: 35.0°................................C104 tr2
    t-V: 33.4°C...............................C0FC t_v1
    V: 1134l/h................................C101 v1
    t-V,BH: 33.4°C............................C0FE t_vbh
    t-DHW: 47.7°C.............................C106 tdhw2

    B1: 12%...................................C0FB bpv
    DHW: 0%...................................069B posmix

    Temperatura mandata attuale: 30.6°C.......01D6 t_hs           da sniffing?
    Temperatura mandata nom.: 42.0°C..........  02 t_hs_set
    Temperatura esterna media: 10.2°C.........0A0C t_ext
    Temperatura ACS attuale: 47.7°C...........  0E t_dhw
    Temperatura ACS nom.: 48.0°C..............  03 t_dhw_set
    Temperatura ritorno: 35.5°C...............  16 t_return

    Temperatura mandata CR attuale: 36.2°C....  0F t_hc
    Temperatura mandata CR nom.: 42.0°C.......  04 t_hc_set
    Temperatura di mandata PHX: 36.1°C........????
    Temperatura di mandata BUH: 36.2°C........????
    Temperatura esterna (opzione): N.A. ......C105 ta2            65136 ~ -400
    Temperatura refrigerante: 29.5°C..........C103 tliq2          0D? 0822?

## 20230106

Dall'analisi del codice di Spanni26 la modifica di un parametro avviene con un messaggio con ID `680` e comando uguale a quello di lettura tranne per il nibble meno significativo del primo byte che vale `0` anziché `1`. Per sicurezza si procede prima ad una modifica da display mentre è attivo il monitor del CAN bus. La modifica del parametro "Temperatura di mandata" da 42.0°C a 43.°C produce, tra gli altri, i seguenti messaggi:

    10A 7 61 00 FA 01 29 00 00
    300 7 22 0A FA 01 29 01 A4
    10A 7 60 00 FA 01 29 01 AE
    10A 7 61 00 FA 01 29 00 00
    300 7 22 0A FA 01 29 01 AE

Il primo messaggio, emesso dal display, è una richiesta del valore del parametro `0129` al modulo di controllo. Questo parametro non compare tra quelli catalogati da Zanac prima e Spanni26 poi, ad ogni modo il valore attuale risulta essere `01A4` (420 in decimale, cioé 42.0°C). Il terzo messaggio si differenzia da quello di lettura per il primo byte passa da `61` a `60` e per gli ultimi due byte che rappresentano il valore `01AE` che corrisponde a 430, cioé 43.0°C, il nuovo valore impostato. Gli ultimi due messaggi sono simili ai primi due: il display richiede nuovamente il valore del parametro al modulo di controllo, probabilmente per mostrarne l'effettivo valore.

È ora di provare a modificare il valore del parametro da terminale:

    >AT SH 680
    OK

    >62 00 FA 01 29 01 A4
    NO DATA

Il valore del parametro sul display passa da 43.0°C a 42.0°C a dimostrazione del fatto che il comando è stato recepito, ma a terminale giunge un `NO DATA`. I sorgenti di Spanni26 suggeriscono che la risposta avrebbe dovuto essere un `OK`. Forse l'ELM327 non è configurato correttamente per questo tipo di comando?

## 20230112

Sostituito l'adattatore USB/OBD con uno appena acquistato che utilizza un integrato CH340 come convertitore seriale/UDB anziché il solito FTDI; non è stato necessario installare alcun driver, il convertitore si presenta sul bus USB come "HL-340 USB-Serial adapter":

    pi@emonpi:~ $ lsusb
    Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
    Bus 001 Device 005: ID 10c4:ea60 Cygnal Integrated Products, Inc. CP2102/CP2109 UART Bridge Controller [CP210x family]
    Bus 001 Device 016: ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter
    Bus 001 Device 003: ID 148f:7601 Ralink Technology, Corp. MT7601U Wireless Adapter
    Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

Il convertitore risponde correttamente a tutti i comandi utilizzati dal programma **daikin_altherma_monitor.py**; una sessione di due ore di monitoraggio del bus CAN ha raccolto 235 campioni, di cui 4 parziali (1.7%, cfr. file **docs/data/daikin/altherma_20230112192245.csv**).

## 20230113

Scoperto che l'Input API di EmonCMS non gradisce ricevere parametri con valore vuoto o *null*. Modificato il dispositivo d'uscita `EmonCMS` in modo da eliminare i parametri privi di valore dal JSON inviato all'API.

## 20230114

Aggiunto un nuovo parametro, "PWM Pompa" che appare sul display della pompa ma che non sembra aver corrispondenza nel catalogo Zanac/Spanni26. Attivata perciò una sessione di sniffing. Sul display il parametro appariva con valore "5%" mentre negli stessi istanti sul bus scorrevano i seguenti messaggi:

    >ATMA
    10A 7 31 00 FA 01 99 00 00
    180 7 22 0A FA 01 99 01 A9
    10A 7 A1 00 FA 06 D0 00 00
    500 7 22 0A FA 06 D0 00 00
    10A 7 31 00 FA C0 F6 00 00
    180 7 22 0A FA C0 F6 00 00
    10A 7 31 00 FA C0 F8 00 00
    180 7 22 0A FA C0 F8 00 00
    10A 7 31 00 FA C0 FA 00 00
    180 7 22 0A FA C0 FA 00 02
    10A 7 31 00 FA 06 96 00 00
    180 7 22 0A FA 06 96 00 00
    10A 7 31 00 FA C1 79 00 00
    180 7 22 0A FA C1 79 00 00
    10A 7 A1 00 FA FD AC 00 00
    500 7 22 0A FA FD AC 00 00
    10A 7 A1 00 FA C1 0C 00 00
    500 7 22 0A FA C1 0C 00 05
    10A 7 31 00 FA C0 F9 00 00
    180 7 22 0A FA C0 F9 00 00
    10A 7 31 00 FA C0 FB 00 00
    180 7 22 0A FA C0 FB 00 64
    10A 7 31 00 FA 06 9B 00 00
    180 7 22 0A FA 06 9B 00 00
    10A 7 31 00 FA 01 48 00 00
    180 7 22 0A FA 01 48 FF BF
    69E 7 51 00 FA 10 0A 00 00
    10A 7 31 00 FA 01 99 00 00
    180 7 22 0A FA 01 99 01 A9
    10A 7 A1 00 FA 06 D0 00 00
    500 7 22 0A FA 06 D0 00 00
    10A 7 31 00 FA C0 F6 00 00
    180 7 22 0A FA C0 F6 00 00
    10A 7 31 00 FA C0 F8 00 00
    180 7 22 0A FA C0 F8 00 00
    10A 7 31 00 FA C0 FA 00 00
    180 7 22 0A FA C0 FA 00 02
    10A 7 31 00 FA 06 96 00 00
    180 7 22 0A FA 06 96 00 00
    10A 7 31 00 FA C1 79 00 00
    180 7 22 0A FA C1 79 00 00
    10A 7 A1 00 FA FD AC 00 00
    500 7 22 0A FA FD AC 00 00
    10A 7 A1 00 FA C1 0C 00 00
    500 7 22 0A FA C1 0C 00 05
    10A 7 31 00 FA C0 F9 00 00
    180 7 22 0A FA C0 F9 00 00
    10A 7 31 00 FA C0 FB 00 00
    180 7 22 0A FA C0 FB 00 64
    10A 7 31 00 FA 06 9B 00 00
    180 7 22 0A FA 06 9B 00 00
    10A 7 31 00 FA 01 48 00 00

L'unico parametro che assume un valore facilmente riconducibile a 5 è il `C10C`:

    10A 7 A1 00 FA C1 0C 00 00
    500 7 22 0A FA C1 0C 00 05

## 20230115

Verificato sperimentalmente che l'Input API di EmonCMS duplica alcuni Input quando riceve valori non validi (accadeva quando il codice sviluppato inviava `None` anziché `null` in corrispondenza di valori non disponibili). Non gradisce nemmeno ricevere un insieme vuoto di parametri, anche se non è chiaro se anche in questo caso si possa assistere alla duplicazione di un Input.

## 20230116

Relativamente ai messaggi d'errore in **/var/log/emoncms/emoncms.log**:

    2023-01-16 21:16:51.093|ERROR|input_controller.php|{"success": false, "message": "Format error, json value is not numeric"} for User: 1

Queste segnalazioni sono associate a parametri valorizzati a `null`. Probabilmente ciò è dovuto al fatto che Solarmon utilizza il formato `json` dell'Input API di EmonCMS che in realtà è un simil-JSON. Il formato che supporta il JSON standard è il `fulljson`. Cambiare da `json` a `fulljson` richiederebbe molto probabilmente la ridefinizione di tutti i *feed*, per questa ragione si decide di lasciare tutto così com'è.

## 20230116

Una veloce verifica ha evidenziato che la versione di EmonCMS attualmente installata sulle due Raspberry (v. 11.2.3) non implementa correttamente la gestione dei `null` nel formato `fulljson`: essi vengono infatti trasformati in `0`, cosa del tutto inaccettabile.
Il problema sembrerebbe rientrato con la [versione 11.3.0](https://community.openenergymonitor.org/t/emoncms-stable-release-v11-3-0/22537).
