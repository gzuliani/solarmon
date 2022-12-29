# Solarmon

## 20220820

Alcuni riferimenti preliminari circa il collegamento all'inverter Huawei SUN2000:

* attraverso il Cloud di Huawei: [https://forum.huawei.com/enterprise/en/communicate-with-fusionsolar-through-an-openapi-account/thread/591478-100027](Communicate with FusionSolar through an openAPI account)
* in locale, via RS485 o Modbus/TCP: [https://forum.huawei.com/enterprise/en/modbus-tcp-guide/thread/789585-100027](MODBUS TCP Guide)

L'inverter è dotato di una Smart Dongle che rappresenta un secondo punto d'accesso locale Modbus/TCP via Wifi; sembra però meno efficiente rispetto a quello offerto dall'inverter, cfr. articolo [https://forum.huawei.com/enterprise/en/is-it-possible-to-make-usb-dongle-tcp-modbus-as-fast-reliable-as-rs-485/thread/822261-100027](Is it possible to make USB Dongle TCP Modbus as fast reliable as RS-485?) sui forum Huawei.

Il forum generale per gli impianti fotovoltaici Huawei è [https://forum.huawei.com/enterprise/en/Digital-Power/forum/100027](Smart PV).

Un lungo e interessante thread circa questo inverter si trova nel forum [https://www.energeticambiente.it/fonti-di-energia-rinnovabile/fotovoltaico/tecnica-componentistica-e-installazione/77889-inverter-huawei-sun2000l/page9](EnergeticAmbiente.it), degni di nota sono i commenti n. 248 e 250.

----

Relativamente al doppio accesso Modbus/TCP inverter/dongle, sembra che il primo in un prossimo futuro venga rimosso:

>Hi. Some hints in order to deal with this problem.
>
>1) Modbus/TCP is still opened from inverter Wifi. That is, SUN20000-XXXXXXXX wifi network has Modbus enabled. Any computer inside this network has access to Modbus interface.
>
>2) Modbus/TCP has been moved from port 502 to port 6607 in firmware SPC116 and later.
>
>3) You can deploy your own network bridge (I did it with a Raspberrry Pi) linked to inverter wifi and regular home network (or plant network) via ethernet cable. And it works.

Fonte: [https://forum.huawei.com/enterprise/en/forum.php?mod=redirect&goto=findpost&ptid=789585&pid=4630919](Forum Huawei).

----

Su Github si trova un client Modbus/TCP scritto in Python per questo inverter, cfr. repository [https://gitlab.com/Emilv2/huawei-solar](huawei-solar).

----

Supporto Modbus in EmonCMS:

* [https://community.openenergymonitor.org/t/modbus-tcp-interfacer/3559](Modbus TCP Interfacer)
* [https://github.com/openenergymonitor/emonhub/tree/master/conf/interfacer_examples/modbus](Emonhub's Modbus interface)

----

L'app Huawei di monitoraggio dell'impianto non si limita a raccogliere i dati dell'inverter; l'articolo [https://forum.huawei.com/enterprise/en/fusionsolar-how-is-selfconsumption-and-self-suffiency-calculated/thread/737443-100027](FusionSolar - How is selfconsumption and self-suffiency calculated) descrive come questi vengono determinati.

## 20220821

La versione di Python 3 installata sulla Raspberry Pi 4 che verrà verosimilmente utilizzata per interrogare l'inverter già comprende il modulo Modbus, tra l'altro in una versione abbastanza recente:

    pi@emonpi:/ $ python3
    Python 3.7.3 (default, Jan 22 2021, 20:04:44)
    [GCC 8.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import pymodbus
    >>> print(pymodbus.__version__)
    2.5.2

La versione stabile più recente è la 2.5.3.

----

Test di connessione verso l'inverter:

    from pymodbus.client.sync import ModbusTcpClient

    inverter_ip = '192.168.0.11'
    inverter_port = '502'

    client = ModbusTcpClient(inverter_ip, port=inverter_port)
    client.connect()
    client.get()
    response = client.read_holding_registers(30000, 15)

Ottengo l'errore:

    client.clModbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)

L'eccezione è sollevata dal metodo `read`, `connect` invece sembra aver successo.
Identico errore anche con timeout di 20 secondi e pausa di 5 secondi tra `connect` e `read`:

    from pymodbus.client.sync import ModbusTcpClient
    import time

    inverter_ip = '192.168.0.11'
    inverter_port = '502'

    client = ModbusTcpClient(inverter_ip, port=inverter_port)
    client.connect()
    time.sleep(5)
    response = client.read_holding_registers(30000, 15, timeout=20)
    print(response)
    client.close()

Utilizzando la porta 6607 l'errore cambia:

    pymodbus.exceptions.ConnectionException: Modbus Error: [Connection] Failed to connect[ModbusTcpClient(192.168.0.11:6607)]

Concludo che la 502 è quella corretta.

----

Se non diversamente specificato `pymodbus` tenta di connettersi al dispositivo con identificativo `0`; l'inverter sembra tuttavia avere assegnato identificativo `1`:

    pi@emonpi:~/FusionSolar $ cat test_modbus.py
    from pymodbus.client.sync import ModbusTcpClient
    import time

    inverter_ip = '192.168.0.11'
    inverter_port = '502'
    wait = 3
    timeout = 20

    client = ModbusTcpClient(inverter_ip, port=inverter_port)
    client.connect()
    time.sleep(wait)
    response = client.read_holding_registers(30000, 15, timeout=timeout, unit=1)
    print(response.registers)
    client.close()
    pi@emonpi:~/FusionSolar $ python3 test_modbus.py
    [21333, 20018, 12336, 12333, 14411, 21580, 11597, 12544, 12337, 12343, 13363, 12336, 11568, 12338, 0]

Convertendo in ASCII la sequenza di byte ricevuta si ottiene la stringa **SUN2000-8KTL-M1 01074300-002**: funziona!

----

Verificato il buon funzionamento del client [https://gitlab.com/Emilv2/huawei-solar](huawei-solar). Il pacchetto ha due dipendenze, backoff e pytz.

----

Punti aperti:

* quali parametri acquisire?
* decodifica dei parametri acquisiti
* politica di campionamento
* politica di serializzazione
* tempi di risposta
* ...

----

Parametri da raccogliere: quelli mostrati nell'app, cioé:

* Battery (%, potenza), PV (potenza), Grid (potenza), Load (potenza)
* Yield (energia) ripartito in Self-consumption/Export (energia, percentuale)
* Consumption (energia) ripartito in Self-sufficiency e Import (energia, percentuale)
* Grafico: PV output power, Consumption, Self-consumption (potenza)

----

Da [https://forum.huawei.com/enterprise/en/fusionsolar-how-is-selfconsumption-and-self-suffiency-calculated/thread/737443-100027](FusionSolar - How is selfconsumption and self-suffiency calculated):

>Consumption Power (Pinv_out - Pmeter) (<0, = 0)
>Self-consumption energy (E_generation_day - E_export_day)(<0, = 0)
>import energy "(Emeter_import|now - Emeter_import|yesterday - Einv_rev_day) (<0 = 0)"
>export energy Emeter_export|now - Emeter_export|yesterday

## 20220822

Valutazione del client [https://gitlab.com/Emilv2/huawei-solar](huawei-solar), disponibile anche già pacchettizzato su PyPi (cfr. [https://pypi.org/project/huawei-solar/](HuaweiSolar)).

Empiricamente si può verificare che per ottenere una comunicazione stabile è sufficiente assegnare ai parametri `wait` e `timeout` un valore uguale o superiore a 1. I valori di default 2/5 utilizzati dal client **huawei-solar** sembrano perciò più che ragionevoli.

La versione minimale del codice per effettuare con successo una lettura è perciò:

    import huawei_solar

    client = huawei_solar.HuaweiSolar(host='192.168.0.11', slave=1)
    result = client.get("model_name")
    print(result.value)

Parametri di potenziale interesse:

* `storage_state_of_capacity` (livello di carica della batteria)
* `storage_charge_discharge_power` (potenza in ingresso/uscita dalla batteria)
* `input_power` (PV)
* `power_meter_active_power` (grid)

Non c'è nessun parametro relativo al carico, quindi non può essere che dedotto dagli altri.

Non mi è chiaro il significato del parametro `active_power`. Di notte risulta essere l'opposto di `storage_charge_discharge_power`, forse rappresenta la potenza in transito nell'inverter.

### Lettura a blocchi di parametri

Una scansione completa di tutti i parametri relativi a correnti/tensioni/potenze (una cinquantina) richiede circa 50 secondi per essere completata. Il client non permette di effettuare delle letture a blocchi, funzionalità prevista dal protocollo Modbus, anche se di un numero limitato di registri:

> Because the maximum length of a Modbus PDU is 253 (inferred from the maximum Modbus ADU length of 256 on RS485), up to 125 registers can be requested at once when using the RTU format, and up to 123 over TCP.

Fonte: [https://en.wikipedia.org/wiki/Modbus](Wikipedia).

----

Dai test risulta che una lettura a blocchi non può essere fatta a partire un indirizzo arbitrario, per esempio dall'indirizzo 30003 (posizione del quarto carattere del nome del modello): l'inverter solleva in questo caso un errore di tipo `IllegalAddress`. Per valutare l'efficienza della lettura multipla rispetto a quella singola conviene considerare un insieme di registri contigui, tutti con dimensione 1 byte, come ad esempio i parametri `PV1-PV4 voltage/current` che coprono un'area di 8 byte a partire dall'indirizzo 32016. Questi i tempi registrati in 5 prove successive:

    Bulk read duration: 0.21s, 8 bytes read
    Scan read duration: 5.96s

    Bulk read duration: 0.50s, 8 bytes read
    Scan read duration: 4.69s

    Bulk read duration: 0.22s, 8 bytes read
    Scan read duration: 5.98s

    Bulk read duration: 0.73s, 8 bytes read
    Scan read duration: 6.37s

    Bulk read duration: 0.17s, 8 bytes read
    Scan read duration: 4.57s

La lettura a blocchi è chiaramente vincente rispetto alla lettura sequenziale dei singoli registri. La durata della lettura a blocchi dipende ovviamente dal numero di byte trasferiti:

    Bulk read duration: 0.21s, 15 bytes read
    Bulk read duration: 0.55s, 100 bytes read

### Scan del Modbus

Modbus prevede la possibilità di richiedere l'elenco dei dispositivi presenti sul bus, cfr. sez. 6.3.6.2 "Command for Querying a Device List" delle specifiche Modbus dell'inverter (documento "SUN2000L V200R001 MODBUS Interface Definitions").

`pymodbus` consente la creazione di comandi definiti dall'utente, cfr. [https://pymodbus.readthedocs.io/en/latest/source/example/custom_message.html](Custom Message Example).

----

Effettuato senza successo una scansione primitiva del modbus richiedendo il valore del registro 32000 incrementando l'identificativo del dispositivo (parametro `unit`). L'unica risposta ottenuta è stata fornita dal dispositivo con identificativo `1` (l'inverter).

## 20220823

Parametri da leggere:

    Signal name                                     | R/W | Type | Unit | Gain | Addr  | Size | huawei_solar.py name                   | Note
    Input power                                     |  RO |  I32 |   kW | 1000 | 32064 |    2 | input_power                            | potenza generata dai pannelli
    Peak active power of current day                |  RO |  I32 |   kW | 1000 | 32078 |    2 | day_active_power_peak                  | picco di potenza dalla mezzanotte
    Active power                                    |  RO |  I32 |   kW | 1000 | 32080 |    2 | active_power                           | potenza in transito nell'inverter
    Accumulated energy yield                        |  RO |  U32 |   kW |  100 | 32106 |    2 | accumulated_yield_energy               | energia prodotta totale
    Daily energy yield                              |  RO |  U32 |   kW |  100 | 32114 |    2 | daily_yield_energy                     | energia prodotta dalla mezzanotte
    [Power meter collection] Active power(*)        |  RO |  I32 |    W |    1 | 37113 |    2 | power_meter_active_power               | potenza da/per la rete
    Positive active electricity                     |  RO |  I32 |  kWh |  100 | 37119 |    2 | grid_exported_energy                   | energia totale verso la rete
    Reverse active power                            |  RO |  I32 |  kWh |  100 | 37121 |    2 | grid_accumulated_energy                | energia totale dalla rete
    [Energy storage] SOC                            |  RO |  U16 |    % |   10 | 37760 |    1 | storage_state_of_capacity              | % carica batteria
    [Energy storage] Charge/Discharge power         |  RO |  I32 |    W |    1 | 37765 |    2 | storage_charge_discharge_power         | potenza da/per la batteria
    [Energy storage] Current-day charge capacity    |  RO |  U32 |  kWh |  100 | 37784 |    2 | storage_current_day_charge_capacity    |
    [Energy storage] Current-day discharge capacity |  RO |  U32 |  kWh |  100 | 37786 |    2 | storage_current_day_discharge_capacity |
    System time                                     |  RW |  U32 |  N/A |    1 | 40000 |    2 | system_time                            | orario di sistema
    [Backup] Switch to off-grid                     |  RW |  U16 |  N/A |    1 | 47604 |    1 | backup_switch_to_off_grid              |

    (*) > 0: feeding power to the power grid, < 0: obtaining power from the power grid

### Accesso diretto all'inverter

Chiarito che all'indirizzo 192.168.0.11:502 risponde la dongle (identificativo 1). L'accesso diretto all'inverter si trova invece all'indirizzo 192.168.200.1:6607 (identificativo 0). Quest'ultimo è effettivamente molto più rapido nelle risposte:

Lettura su dongle (192.168.0.11:502, id:1):

* aggregato 8 registri da 1 byte: 0.36s
* sequenzale 8 registri da 1 byte: 5.51s
* blocco di 15 byte: 0.21
* blocco di 100 byte: 0.55

Lettura su inverter (192.168.200.1:6607, id:0):

* aggregato 8 registri da 1 byte: 0.07s
* sequenzale 8 registri da 1 byte: 0.64s
* blocco di 15 byte: 0.05
* blocco di 100 byte: 0.21

Peccato che questo punto d'accesso sia destinato alla chiusura.

### Scansione del bus dell'inverter

Sulla rete dell'inverter si ottiene risposta solo dal dispositivo con identificativo 0. Il dispositivo con identificativo 11 (identificativo riportato sul display del contatore 1 che è collegato via linea RS485 all'inverter) non risponde quando gli viene richiesto il valore del registrio 37100 che, da specifiche, è uno dei registri supportati dal contatore. La richiesta di lettura del registro 37000 (uno dei registri della batteria) non ottiene risposta su nessun identificativo, evidentemente nemmeno la batteria si trova su questo bus.

## 20220824

Non è ancora chiaro il significato del parametro `active_power`. L'acquisizione

    local_time          input_power active_power power_meter_active_power storage_charge_discharge_power
    2022-08-23 20:49:58 0           364          0                       -363

suggerisce che:

    active_power = -storage_charge_discharge_power + ...

----

Sempre a proposito del parametro `active_power`: la mattina risulta essere negativa, fino a quando le batterie raggiungono la carica del 95%: si tratta probabilmente dell'energia dell'impianto vecchio che viene utilizzata per caricare le batterie. Evidentemente la mattina presto il nuovo impianto non fornisce sufficiente energia per saturare la capacità di carica della batteria.

Sembra dunque che `active_power` rappresenti il flusso di energia tra il mondo DC di Huawei e il mondo AC esterno. L'energia che fluisce direttamente dai pannelli nuovi alla batteria non contribuisce infatti al computo dell'`active_power`.

## 20220825

Colpo di scena:

>Unit id is an obligatory field of the Modbus command. It's the address of the target device (an equivalent of the IP address, so to speak). I believe you are using a library that defaults to unit id 0, but SDongle, over Modbus-TCP, responds to unit id 100 (as per SDongleA V100R001C00 MODBUS Interface Definitions document). Unit id 1 is its first child device, in our case it's the inverter.

Fonte: [https://forum.huawei.com/enterprise/en/forum.php?mod=redirect&goto=findpost&ptid=745393&pid=4046067](Firmware V100R001C00SPC120).

In effetti, a ben guardare, la stessa informazione è riportata a pag. 12 del documento "SDongleA - V100R001C00 - MODBUS Interface Definitions". Riassumendo, quindi: **il punto d'accesso al Modbus/TCP del sistema Huawei si trova all'indirizzo 192.168.0.11:502; l'unità `1` è la dongle, l'unità `100` l'inverter**.

I registri interessanti della dongle sono:

    'Total input power',   'U32', 'kW', 1000, 37498, 2
    'Load power',          'U32', 'kW', 1000, 37500, 2
    'Grid power',          'I32', 'kW', 1000, 37502, 2
    'Total battery power', 'I32', 'kW', 1000, 37504, 2
    'Total active power',  'I32', 'kW', 1000, 37504, 2

Interrogata, la dongle fornisce i seguenti valori:

    Total input power: 2.88kW
    Load power: 0.253kW
    Grid power: -2.627kW
    Total battery power: 0.0kW
    Total active power: 0.0kW

All'incirca nello stesso momento (l'orologio indica le 15:05) la risposta dell'inverter è:

    Input power: 2103
    Active power: 6905.25
    Power meter active power: 2622
    [Storage] Charge/Discharge power: 0

`grid_power` risulta essere l'opposto di `power_meter_active_power`, plausibile.

La speranza è quella di poter scorporare la potenza del vecchio impianto da "Total input power" ottenuto dalla dongle sottraendo l'"Input power" dall'inverter. Purtroppo i contatori sono stati staccati dalla Raspberry dopo che l'aggiunta del terzo causava l'innalzamento della temperatura (causata da `rsyslog`, probabilmente per un numero troppo elevato di scritture da parte di `emond`, a loro volta causata da errori di riconoscimento degli impulsi, forse dovuti all'aggiunta del nuovo contatore trifase).

Considerando che la potenza nominale del nuovo impianto è all'incirca due volte e mezza quella dell'impianto vecchio, le misure sembrano sensate: ad una successiva interrogazione la potenza in ingresso secondo la dongle ammontava a 2.816kW 2050W secondo l'inverter; il rapporto tra le due rilevazioni non dista molto da quello nominale.

----

Tempi medi di lettura di 11 parametri:

* via dongle: 10.7s (stdev: 2.0s)
* via inverter: 3.2s (stdev: 0.7s)

Queste statistiche non fanno che confermare che è un peccato che Huawei abbia deciso di non supportare più la connessione diretta Modbus/TCP all'inverter.

## 20220826

L'acquisizione di ieri sera si è arrestata a causa di un errore di timeout (cfr. file 20220827_2.csv). L'inserimento di una pausa di 3 secondi tra la lettura dei parametri della dongle e quelli dell'inverter non ha sortito effetto alcuno.

Considerare la possibilità di utilizzare due connessioni distinte, una per la dongle, una per l'inverter (per quanto questo rappresenti una soluzione destinata al fallimento: ad un certo punto la connessione diretta all'inverter cesserà di funzionare).

----

Sempre dalle specifiche della dongle:

>In unicast mode, a slave node returns one response for each request from the master node. If the master node does not receive any response from the slave node in 5s, the communication process is regarded as timed out.

Sembra inutile configurare il timeout a 20 secondi, internamente la dongle fissa quel parametro a 5.

----

Provato ad interrogare la dongle su un indirizzo dell'inverter: ottenuto un errore `IllegalAddress`, la dongle quindi non è un proxy puro dell'inverter.

### Doppia connessione dongle/inverter

Utilizzando due connessioni distinte, dopo un'ora e mezza di funzionamento non si è verificato ancora nessun errore.

### Limitare il numero di letture

Forse è l'alto numero di transazioni consecutive a saturare la dongle e conseguentemente a causare l'errore di comunicazione?

I registri della dongle possono essere letti tutti insieme:

    Total input power                                 37498
    Load power                                        37500
    Grid power                                        37502
    Total battery power                               37504
    Total active power                                37506

Per l'inverter invece servono delle letture multiple, almeno quattro:

    Input power                                       32064
    Peak active power of current day                  32078
    Active power                                      32080
    Accumulated energy yield                          32106
    Daily energy yield                                32114
    [Power meter collection] Active power             37113
    Positive active electricity                       37119
    Reverse active power                              37121

    [Energy storage] SOC                              37760
    [Energy storage] Charge/Discharge power           37765
    [Energy storage] Current-day charge capacity      37784
    [Energy storage] Current-day discharge capacity   37786

    System time                                       40000

    [Backup] Switch to off-grid                       47604

----

Sembra che la dongle non gradisca le letture a blocchi:

    pymodbus.exceptions.ConnectionException: Modbus Error: [Connection] ModbusTcpClient(192.168.0.11:502): Connection unexpectedly closed 0.031604 seconds into read of 8 bytes without response from unit before it closed connection

## 20220827

La connessione diretta all'inverter sembra non soffrire del problema del timeout: effettuando rapide sequenze di letture miste singole/a blocchi intervallate tra loro da 10 secondi di pausa non ha evidenziato problemi. Nessun problema nemmeno utilizzando la connessione della dongle (i tempi ovviamente si sono allungati sensibilmente).

Anche la dongle sta rispondendo bene, oggi:

* lettura di singoli registri: ok (3s circa a lettura)
* lettura di gruppi di registri: ok (3s circa a lettura)

Pure l'interrogazine mista dongle/inverter sta funzionando a dovere, oggi.

----

I problemi di timeout registrati ieri forse sono dovuti ad un sovraccarico del sistema: i servizi `emond` erano attivi e avevano riempito il syslog quasi saturando la partizione.

## 20220828

Il problema di comunicazione era dovuto ad un conflitto: emonhub era configurato per interrogare la dongle!

### Script Python come servizio

Impostazione dello script come servizio (systemd):

[https://wiki.archlinux.org/title/systemd]
[https://www.wyre-it.co.uk/blog/converting-from-sysvinit-to-systemd/]

1. salvare il contenuto che segue nel file `huawei_sun2000.service` in `/lib/systemd/system`:

        [Unit]
        Description=Huawei SUN2000 monitor
        After=network-online.target syslog.target

        [Service]
        Type=simple
        WorkingDirectory=/home/pi/huawei
        ExecStart=/usr/bin/python3 /home/pi/huawei/main.py
        StandardOutput=syslog
        StandardError=syslog
        Restart=on-failure

        [Install]
        WantedBy=multi-user.target

2. registrare il nuovo servizio con:

        sudo systemctl daemon-reload

Per avviare, arrestare, ... il servizio:

    sudo systemctl start|stop|restart|status huawei_sun2000

Per attivare l'avvio automatico al boot:

    sudo systemctl enable huawei_sun2000

Per disabilitare l'avvio automatico:

    sudo systemctl disable huawei_sun2000

## 20220829

Ora che l'acquisizione si svolge su lunghi periodi di tempo si evidenzia una certa perdita di campioni, sia da parte della dongle che dell'inverter. Non tantissimi, ma comunque una parte significativa:

    start: 2022-08-28T22:54:04
    end: 2022-08-29T19:18:28
    samples: 1226
    dongle misses: 186 (15.1%)
    inverter misses: 224 (18.3%)
    meter misses: 0

In [https://github.com/evcc-io/evcc/discussions/1928](Huawei Inverter with smart dongle - Modbus TCP) consigliano di non interrogare la dongle troppo frequentemente.

Controintuitivamente(?!), riducendo il periodo tra un'interrogazione e la successiva da 60 a 10 secondi, gli errori sono scomparsi. Aumentando il periodo a 30 secondi gli errori sono ricomparsi, ma molto più sporadicamente.

## 20220830

ore 10:00 circa

Su 1220 campioni acquisiti con periodo di 20 secondi sono stati registrati 11 errori di comunicazione con la dongle (0.9%), 17 con l'inverter (1.4%). Decisamente meglio.

## 20220901

Viene il dubbio che il periodo di 60 secondi (un'acquisizione effettuata allo scadere di un minuto) possa andare in conflitto con qualche procedura interna della dongle effettuata con la stessa cadenza. Per questa ragione è stata predisposta un'acquisizione di qualche ora con periodo di 67 secondi; su un totale di 967 campioni sono stati riscontrati 6 errori di comunicazione con la dongle (0.6%), 16 con l'inverter (1.6%). I tassi sono compatibili con quelli registrati ieri.

----

Per semplificare la ricombinazione dei feed in EmonCMS, le definizioni dei registri con valori di potenza espresse in W sono state modificate in modo da produrre kW moltiplicando il gain per 1000.

Inverter:

* power_meter_active_power
* storage_charge_discharge_power

Contatore pompa di calore

* a_phase_active_power
* b_phase_active_power
* c_phase_active_power

## 20220902

Continua l'analisi del tasso di errori di comunicazione in funzione del periodo di campionamento. Ad oggi i risultati sono:

    sampling policy     samples dongle_misses inverter_misses dongle_misses(%) inverter_misses(%)
    when minute expires    1226           186             224           15.17%             18.27%
    every 30s              2284            21              32            0.92%              1.40%
    every 67s               967             6              16            0.62%              1.65%
    every 15s              4852            56              87            1.15%              1.79%

----

Rimosso il parametro `system_time` tra quelli campionati, non serve.

## 20220903

Grazie al contatore ad impulsi presente sulla linea del vecchio impianto si può rinunciare ai dati forniti dalla dongle in quanto, indicato con `power` la potenza fornita dal vecchio impianto (attualmente ricavata da un contatore a impulsi):

* `total_input_power` = `power` + `input_power`
* `load_power` = `power` + `input_power` - `storage_charge_discharge_power` - `power_meter_active_power`
* `grid_power` = -`power_meter_active_power`
* `total_battery_power` = `storage_charge_discharge_power`

Non sarebbe male svincolarsi dalla dongle perché, a giudicare dai grafici prodotti da EmonCMS in questi giorni di prove sembra applichi una sorta di filtro passa basso ai dati, a spanne una media mobile determinata su una finestra di 5 minuti.

## 20220904

Semplificato l'accesso all'inverter: prima era mediato da un access point, ora è realizzato tramite una dongle Wifi connessa ad una delle porte USB della Raspberry Pi. La connessione non è molto stabile, a volte cade senza apparente ragione; nel log si legge:

    2022-09-04T17:51:12 ERROR Could not read inverter, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)
    2022-09-04T17:51:12 INFO Reconnecting after a bad TCP response...

Contemporaneamente l'applicativo segnala l'assenza di collegamento:

    2022-09-04T17:51:12 ERROR Could not read inverter, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)
    2022-09-04T17:51:12 INFO Reconnecting after a bad TCP response...
    
Negli stessi istanti si nota l'assenza dei dati dell'inverter nel file CSV:

    2022-09-04T17:51:14.596105,,,,,,,,,,,,,,,,,,0.002,0.001,0.029,11.12375
    2022-09-04T17:51:44.784021,,,,,,,,,,,,,,,,,,0.001,0.002,0.029,11.12375

----

Cambiato l'adattatore USB/Wifi, dopo due ore di acquisizione continua non è stato registrato alcun errore di comunucazione o perdita di campioni.

## 20220905

Con il nuovo adattatore e utilizzando la connessione diretta all'inverter finalmente un risultato di tutto rispetto:

    start: 2022-09-04T19:39:01
    end: 2022-09-05T19:06:14
    samples: 2764
    dongle misses: n/a
    inverter misses: 0
    meter misses: 0

## 20221003

La nuova versione del servizio Solarmon su una Raspberry reinstallata di fresco mostra qualche problema: dopo poco più di una giornata di lavoro nel log sono stati registrati oltre 130 errori di comunicazione con i contatori monofase:

    2022-10-02T17:26:48 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T17:33:28 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T17:46:17 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T17:56:30 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T18:12:57 ERROR Could not read house, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T18:46:47 ERROR Could not read house, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-02T19:00:07 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    ...

Non sono presenti errori relativi alla comunicazione con l'inverter Huawei o il contatore trifase. Per verificare se si tratta di un problema legato alla presenza di più dispositivi collegati alla dongle, la pausa tra una lettura e l'altra su /dev/ttyUSB è stata aumentata da 1 a 3 secondi. Non dovesse rivelarsi risolutivo, una successiva prova consisterà nell'aumentare il timeout sui contatori monofase, attualmente impostato a 1 secondo.

----

Pochi minuti dopo l'allungamento della pausa si sono verificati altri errori di comunicazione:

    2022-10-03T22:23:45 ERROR Could not read old-pv, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)
    2022-10-03T22:29:55 ERROR Could not read house, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No respons
e received, expected at least 2 bytes (0 received)
    2022-10-03T22:41:09 ERROR Could not read house, reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)

Lo lascio proseguire per verificare se il tasso d'errori diminuisce con la nuova impostazione.

Tasso odierno con `delay_between_reads` a 1: 132/29*24=109 errori/giorno.

## 20221004

Dopo circa una giornata sembra confermato che la nuova impostazione non ha sortito alcun effetto:

    start               end                 duration errors errors/day       note
    2022-10-02T17:21:02 2022-10-03T22:20:01 28:58:59 131    108.477175360658 delay_between_reads=1
    2022-10-03T22:20:02 2022-10-04T19:13:37 20:53:35 93     106.829754702437 delay_between_reads=3

## 20221005

L'aumento del timeout sembra aver peggiorato le cose:

    start               end                 duration errors errors/day       note
    2022-10-04T21:05:18 2022-10-05 08:28:20 11:23:02 78     164.442926162119 -

## 20221208

Si apre un nuovo fronte, l'acquisizione dei parametri di funzionamento della pompa di calore, una Daikin Altherma.

I primi riferimenti sono dei repository di alcune implementazioni già esistenti:

* https://github.com/zanac/pyHPSU
* https://github.com/Spanni26/pyHPSU
* https://github.com/raomin/ESPAltherma

Sembra assodato che il protocollo CAN non sia documentato, non c'è nulla di ufficiale reperibile in rete.

## 20221209

Un collaboratore di zanac spiega nel dettaglio come hanno proceduto. Hanno optato per una daugther board CAN/Ethernet (PiCAN2):

* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-prima-parte/
* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-seconda-parte/
* https://lamiacasaelettrica.com/daikin-hpsu-compact-hack-terza-parte/

I tre articoli sono l'estratto del thread:

* https://cercaenergia.forumcommunity.net/?t=58409485

Le prime due implementazioni (zanac e Spanni26) sfruttano l'interfaccia CAN (connettore J13) nella doppia modalità Ethernet/CAN (con la daughter board) e seriale/OBD con un adattatore basato sull'integrato ELM327. Il terzo (raomin) sfrutta invece una connessione seriale (connettore X10A) che, a detta di Spanni26, è particolarmente inefficiente rispetto al CAN, richiedendo centinaia di millisecondi per la lettura di un singolo parametro.

## 20221210

Trovata una nuova implementazione che utilizza una connessione seriale proprietaria Daikin;

* https://github.com/Arnold-n/P1P2Serial (o https://github.com/budulinek/Daikin-P1P2---UDP-Gateway, README.md più chiaro)

La connessione al bus P1P2 elettricamente non è banale (Arnold-n suggerisce l'uso di optoisolatori) e per questa ragione immediatamente scartata.

## 20221211

Andrea ha in casa un convertitore seriale/OBD basato sull'ELM327: è un "FORD modified ELM327". Ottimo, sarà oggetto di una verifica di fattibilità quanto prima.

## 20221212

[Studio delle specifiche dell'ELM327]

## 20221213

I comandi di inizializzazione dell'ELM327 secondo i sorgenti di Spanni26 (più recenti rispetto a quelli di zanac, ma di fatto quasi identici) risultano essere i seguenti:

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

Collegamenti elettrici connettore J13/pres OBD:

    CAN-H ...... pin 6
    CAN-L ...... pin 14
    CAN-GND .... pin 5
    CAN-VCC .... <non necessario>

L'interruttore HS-CAN/MS-CAN sul convertitore OBD/USB "Ford modified ELM327" va impostato su "HS-CAN".

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

La velocità del bus CAN per il protocollo `C` "User1 CAN" è regolata dal registro `2F`, che va impostato secondo le stesse modalità:

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

Nè i sorgenti di zanac né quelli di Spanni26 si preoccupano di impostare questo parametro, forse perché fatto una volta per tutte all'inizio (tutti i parametri programmabili sono persistenti e il loro valore non viene perso nemmeno dopo uno spegnimento). Forse la ragione per cui le sequenze esadecimali non sono state riconosciute durante il primo test dipende dall'errata impostazione della velocità del bus e non dal fatto che l'ELM327 si aspetta delle sequenze binarie pure.

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

I `NO DATA` non dovrebbero dipendere da problemi relativi agli identificativi dei parametri: per quando zanac e Spanni26 utilizzino un modello diverso di pompa di calore, i pacchetti acquisiti per la Altherma differiscono da quelli riportati nelle analisi di zanac solamente per i valori assunti dai parametri, ma gli identificativi corrispondono perfettamente, anche quelli dei nodi della rete.

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

Grazie al comando `PB` risulta più comodo utilizzare il protocollo `B` rispetto al `C`; la configurazione, per quanto non persistente, è infatti più immediata:

    AT PB 80 19
    AT SP B

Il cambio di protocollo non produce effetti collaterali sullo sniffing, al momento viene promosso a soluzione preferita.

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

# 20221228

Approntato una versione dello sniffer con un thread di polling che pubblica i valori dei parametri raccolti.

# 20221229

Rifattorizzato il codice suddividendolo nelle componenti elm327.py, daikin_altherma.py e daikin_altherma_sniffer.py.
