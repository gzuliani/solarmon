# Solarmon - Dashboard con InfluxDB e Grafana

Ultima modifica : 02/05/2025

[!WARNING] Prendere queste istruzioni *cum grano sali*: le dinamiche dell'evoluzione del software libero tendono a renderle sempre più rapidamente obsolete.

L'attuale implementazione di [Solarmon](https://github.com/gzuliani/solarmon) consente il salvataggio dei dati acquisiti in un file CSV o il loro invio alle API di [EmonCMS](https://emoncms.org/). Nell'ottica di svincolarsi da quest'ambiente ho voluto verificare se è possibile estendere Solarmon in modo da salvare i dati in un'istanza [InfluxDB](https://www.influxdata.com/) e usare [Grafana](https://grafana.com/) per costruire una dashboard simile a quelle che si possono definire in EmonCMS.

## Indice

- [Solarmon - Dashboard con InfluxDB e Grafana](#solarmon---dashboard-con-influxdb-e-grafana)
  - [Indice](#indice)
  - [Hardware](#hardware)
  - [Software di base](#software-di-base)
    - [Supporto RTC DS3231](#supporto-rtc-ds3231)
    - [Adattatore USB/RS485](#adattatore-usbrs485)
    - [Funzioni di utilità](#funzioni-di-utilità)
      - [Rilevamento della temperatura](#rilevamento-della-temperatura)
      - [Rilevamento del livello del segnale WiFi](#rilevamento-del-livello-del-segnale-wifi)
  - [Software applicativo](#software-applicativo)
    - [InfluxDB](#influxdb)
      - [Installazione di InfluxDB](#installazione-di-influxdb)
      - [Configurazione di InfluxDB](#configurazione-di-influxdb)
    - [Grafana](#grafana)
      - [Installazione di Grafana](#installazione-di-grafana)
      - [Configurazione di Grafana](#configurazione-di-grafana)
      - [Grafana sulla porta 80](#grafana-sulla-porta-80)
    - [Solarmon](#solarmon)
      - [Strategie iniziali](#strategie-iniziali)
    - [Dataplicity](#dataplicity)
      - [Errore "Device not connected"](#errore-device-not-connected)
  - [Appendice A - Note su InfluxDB](#appendice-a---note-su-influxdb)
    - [Note generali](#note-generali)
    - [Importazione CSV](#importazione-csv)
    - [Esportazione CSV](#esportazione-csv)
    - [Cancellazione dei dati](#cancellazione-dei-dati)
    - [Spazio occupato su disco](#spazio-occupato-su-disco)
    - [Backup](#backup)
    - [Restore](#restore)
    - [Ripristino della serie storica "raw\_data"](#ripristino-della-serie-storica-raw_data)
      - [Creazione dell'istanza InfluxDB](#creazione-dellistanza-influxdb)
      - [Ripristino di backup precedenti l'ultimo](#ripristino-di-backup-precedenti-lultimo)
      - [Ripristino del backup più recente](#ripristino-del-backup-più-recente)
      - [Export CSV](#export-csv)
    - [Task di aggregazione giornaliero](#task-di-aggregazione-giornaliero)
    - [Determinazione degli intervalli senza campioni](#determinazione-degli-intervalli-senza-campioni)
  - [Appendice B - Note su Grafana](#appendice-b---note-su-grafana)
  - [Appendice C - Note sull'inverter](#appendice-c---note-sullinverter)
    - [Punti di attenzione](#punti-di-attenzione)
    - [Stima dei consumi](#stima-dei-consumi)
    - [Anomalie](#anomalie)
    - [`load_power` nullo](#load_power-nullo)
  - [Appendice D - Passaggio dall'ora legale a quella solare](#appendice-d---passaggio-dallora-legale-a-quella-solare)
  - [Appendice E - Acquisizione dati dall'OsmerFVG](#appendice-e---acquisizione-dati-dallosmerfvg)
  - [Appendice F - Esempio di query "complessa"](#appendice-f---esempio-di-query-complessa)
  - [Appendice G - Stabilizzazione della connessione WiFi](#appendice-g---stabilizzazione-della-connessione-wifi)
    - [Disabilitare il Power Management del modulo WiFi](#disabilitare-il-power-management-del-modulo-wifi)
    - [Disabilitare il protocollo IPv6](#disabilitare-il-protocollo-ipv6)
    - [Riavviare il sistema](#riavviare-il-sistema)
  - [Appendice H - Ripristino del sistema in seguito al guasto della scheda SD](#appendice-h---ripristino-del-sistema-in-seguito-al-guasto-della-scheda-sd)
    - [Ripristino dell'ultimo backup di InfluxDB](#ripristino-dellultimo-backup-di-influxdb)
    - [Ripristino dell'ultimo backup di Grafana](#ripristino-dellultimo-backup-di-grafana)

## Hardware

Il sistema girerà su una Raspberry Pi 4 con 2GB di RAM acquistata per l'occasione, corredata del solito RTC DS3231. Necessitando la scheda di raffreddamento, ho optato per una soluzione passiva, un case in lega di alluminio:

![Raspberry Pi 4 aluminum case](img/rasp_case.png)

Un breve stress test a suon di

    pi@raspberry:~ $ yes >/dev/null &

ne ha dimostrato l'efficacia: in sua assenza la scheda si è bloccata dopo un paio di minuti, quando ancora tre dei quattro core erano ancora completamente scarichi; con il dissipatore installato, dopo un minuto con carico CPU massimo, la temperatura è rimasta al di sotto dei 62°C:

![Temperature vs. CPU load](img/rasp_temp_vs_cpu_load.png)

## Software di base

Il sistema operativo prescelto è "Raspberry Pi OS" (ex Raspian), installato manualmente copiando su una scheda SD da 32GB l'immagine più recente disponibile nella [pagina dedicata](https://www.raspberrypi.com/software/operating-systems/) del sito ufficiale.

### Supporto RTC DS3231

Il primo passo consiste nell'attivare il supporto IC2 dall'interfaccia di configurazione di Raspberry Pi OS che si richiama col comando:

    pi@raspberry:~ $ sudo raspi-config

Selezionare la voce "5. Interfacing Options", quindi "P5 I2C", "Yes". Confermare con "Ok". A questo punto impartire i seguenti comandi:

    pi@raspberry:~ $ sudo reboot
    pi@raspberry:~ $ sudo i2cdetect -y 1

Alla posizione 68 della tabella emessa dal comando precedente deve comparire il codice `68` oppure `UU`:

        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    00:          -- -- -- -- -- -- -- -- -- -- -- -- --
    10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
    70: -- -- -- -- -- -- -- --

Continuare con i comandi:

    pi@raspberry:~ $ sudo modprobe rtc-ds1307
    pi@raspberry:~ $ sudo bash
    pi@raspberry:~ $ echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
    pi@raspberry:~ $ exit

Verificare l'orario dell'orologio:

    pi@raspberry:~ $ sudo hwclock -r

Se la data non è corretta allinearla a quella di sistema (presumendo che questa sia corretta) con il comando:

    pi@raspberry:~ $ sudo hwclock -w

Completare la configurazione con i seguenti interventi:

- aggiungere la dicitura `rtc-ds1307` in coda al file **/etc/modules**
- aggiungere il frammento

      echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
      sudo hwclock -s
      date

  in coda al file **/etc/rc.local**, prima del comando di uscita `exit`.

### Adattatore USB/RS485

Poiché Linux attribuisce un nome di dispositivo arbitrario — potenzialmente diverso ad ogni accensione — all'adattatore USB/RS485 che verrà utilizzato per raccogliere i dati dall'inverter e dai contatori di potenza, conviene associargli un nome simbolico fisso, per esempio **ttyUSB_RS485**. Dopo aver connesso l'adattatore alla scheda si ricavano gli identificativi del costruttore e del prodotto con il comando:

    pi@raspberry:~ $ lsusb
    Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
    Bus 001 Device 007: ID 1a86:7523 QinHeng Electronics CH340 serial converter
    Bus 001 Device 003: ID 148f:7601 Ralink Technology, Corp. MT7601U Wireless Adapter
    Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

Si tratta in questo caso del secondo dispositivo in elenco.

Creare il file **/etc/udev/rules.d10-usb-serial.rules** dal seguente contenuto:

    # QinHeng Electronics CH340 serial converter
    SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyUSB_RS485"

Forzare il caricamento della nuova definizione con il comando:

        pi@raspberry:~ $ sudo udevadm trigger

A questo punto il dispositivo è riconosciuto come **/dev/ttyUSB_RS485** anziché **/dev/ttyUSB0**.

**Nota**: sebbene correttamente individuato dal sistema operativo, l'adattatore non è stato associato al dispositivo **/dev/ttyUSB0** in Ubuntu 22.04, a differenza di quanto accaduto in Raspberry Pi OS. Il problema (descritto per esempio [qui](https://askubuntu.com/questions/1403705/dev-ttyusb0-not-present-in-ubuntu-22-04)) sta nel fatto che a quella stessa coppia è stato associato un altro dispositivo. La soluzione consiste nel commentare la riga

    ENV{PRODUCT}=="1a86/7523/*", ENV{BRLTTY_BRAILLE_DRIVER}="bm", GOTO="brltty_usb_run"

nel file **/usr/lib/udev/rules.d/85-brltty.rules**.

### Funzioni di utilità

#### Rilevamento della temperatura

Per ricavare il valore del sensore di temperatura utilizzare indifferentemente:

    pi@raspberry:~ $ cat /sys/class/thermal/thermal_zone0/temp

che riporta la temperatura in millesimi di gradi centrigradi, oppure il più amichevole:

    pi@raspberry:~ $ vcgencmd measure_temp

I valori ottenuti dai due metodi combaciano. Valori ottimali della temperatura sono quelli al di sotto dei 50°C. Quelli accettabili al di sotto dei 60°C.

#### Rilevamento del livello del segnale WiFi

    pi@raspberry:~ $ iwconfig 2>/dev/null | grep -oP "Signal level=\K(.*)\s+$"

Una classificazione di massima di qualità del segnale ricevuto è:

- 30 dBm: eccellente
- 67 dBm: buono
- 70 dBm: accettabile
- 80 dBm: critico
- 90 dBm: insufficiente

Fonte: [MetaGeek](https://www.metageek.com/training/resources/understanding-rssi/)

## Software applicativo

### InfluxDB

#### Installazione di InfluxDB

InfluxDB 2.x richiede un sistema operativo a 64 bit. La versione corrente di InfluxDB è la 2.7. Per installarla è sufficiente seguire le istruzioni dal [sito ufficiale](https://docs.influxdata.com/influxdb/v2.7/install/):

    pi@raspberry:~ $ cd ~/Downloads

>     # Ubuntu/Debian AMD64
>     wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.0-arm64.deb
>     sudo dpkg -i influxdb2-2.7.0-arm64.deb
>     sudo service influxdb start

Riavviare la scheda e assicurarsi che il servizio sia attivo:

    pi@raspberry:~ $ sudo service influxdb status
         ...
         Active: active (running) since Sat 2023-08-05 18:15:13 CEST; 31s ago

Per comodità conviene installare anche l'interfaccia a riga di comando (istruzioni alla pagina [](https://docs.influxdata.com/influxdb/v2.7/tools/influx-cli/)):

    pi@raspberry:~ $ wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-arm64.tar.gz
    pi@raspberry:~ $ mkdir influxdb2-client-2.7.3
    pi@raspberry:~ $ tar -xf influxdb2-client-2.7.3-linux-arm64.tar.gz --directory ./influxdb2-client-2.7.3
    pi@raspberry:~ $ sudo cp influxdb2-client-2.7.3/influx /usr/local/bin/

#### Configurazione di InfluxDB

Conettersi alla GUI di InfluxDB all'indirizzo `http://<raspberry-pi-IP>:8086` e inserire le credenziali del primo utente del database:

- username: pi
- organization name: home
- bucket name: raw_data

In seguito alla creazione dell'utente InfluxDB fornisce l'*API token* amministrativo (detto anche `OPERATOR-TOKEN` o `ROOT-TOKEN`) che garantisce i privilegi di amministratore, e dovrà essere specificato ogni qualvolta si invocherà il comando `influx` da terminale. È tuttavia possibile associare questo token alla connessione di default in modo da risparmiarsi la fatica di indicarlo ogni volta:

    pi@raspberry:~ $ influx config create \
      --config-name default \
      --host-url http://localhost:8086 \
      --org home \
      --token <ROOT-TOKEN> \
      --active

**Conservare il token in un luogo sicuro!**

Conviene a questo punto creare un altro token, quello che utilizzerà Solarmon per autenticarsi all'API di InfluxDB. Entrare nella sezione **API TOKENS** della pagina **Load Data** e premere il pulsante **GENERATE API TOKEN**, quindi selezionare la voce "All Access API Token"; fornire un nome per il token (ad esempio "Solarmon"). Conservare il token per l'uso in Solarmon (cfr. parametro `influx_api_token` in **main.py**).

### Grafana

#### Installazione di Grafana

La versione più recente di Grafana è la 11.6.1. Le istruzioni per l'installazione su Raspberry Pi Desktop sono reperibili sul [sito ufficiale](https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/#2-start-the-server):

>     sudo apt-get install -y apt-transport-https
>     sudo apt-get install -y software-properties-common wget
>     sudo wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
>     echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
>     sudo apt-get update
>     sudo apt-get install grafana

Le istruzioni proseguono nella pagina [Start the Grafana server](https://grafana.com/docs/grafana/latest/setup-grafana/start-restart-grafana/):

> The following instructions start the grafana-server process as the grafana user, which was created during the package installation.
>
> To start the service, run the following commands:
>
>
>     sudo systemctl daemon-reload
>     sudo systemctl start grafana-server
>     sudo systemctl status grafana-server
>
> [...]
>
> To configure the Grafana server to start at boot, run the following command:
>
>     sudo systemctl enable grafana-server

Sulla Raspberry Pi fisica l'avvio del server è avvenuto con successo, a differenza di quanto accaduto con Raspberry Pi Desktop su macchina virtuale VirtualBox nelle prove preliminari:

>     pi@raspberry:~ $ sudo systemctl status grafana-server
>     ● grafana-server.service - Grafana instance
>          Loaded: loaded (/lib/systemd/system/grafana-server.service; disabled; vend>
>          Active: failed (Result: signal) since Sat 2023-07-29 16:01:12 CEST; 4s ago

la causa è da ricondurre a una configurazione di Grafana incompatibile con l'ambiente virtuale. Personalmente sono riuscito a far avviare il server Grafana commentando la seguente impostazione nel file **/usr/lib/systemd/system/grafana-server.service**:

    SystemCallArchitectures=native

#### Configurazione di Grafana

La pagina di riferimento è [Use Grafana with InfluxDB OSS](https://docs.influxdata.com/influxdb/v2.7/tools/grafana/). Alcune considerazioni che emergono dall'analisi delle informazioni disponibili in rete sono:

- InfluxDB supporta due linguaggi di interrogazione: *InfluxQL* (una sorta di SQL) e *Flux* (funzionale). Il primo è nato su InfluxDB 0.x e 1.x, per poterlo usare sulla versione 2.x occorre mappare il vecchio concetto di *database* sull'attuale *bucket* (cfr. pagina [Manage DBRP mappings](https://docs.influxdata.com/influxdb/v2.7/query-data/influxql/dbrp/));

- InfluxQL non è utilizzabile dalla GUI di InfluxDB, che supporta solo Flux.

La scelta è ricaduta su Flux, in quanto permette di definire query molto più articolate di quanto possibile con InfluxQL.

Occorre innanzitutto generare un token di accesso ad InfluxDB: entrare nella sezione **API TOKENS** della pagina **Load Data** del portale InfluxDB e premere il pulsante **GENERATE API TOKEN**, quindi selezionare la voce "Custom API Token". Fornire un nome per il token (ad esempio "Solarmon Read Only") e concedere l'accesso in lettura ai bucket necessari (**raw_data** e **daily_data**, vedi più avanti).

Autenticarsi quindi nella GUI di Grafana con le credenziali di amministrazione e aggiungere una nuova *Data source* InfluxDB con le seguenti proprietà:

- **Query Language**: `Flux`
- **URL**: `http://localhost:8086`

Nella sezione **InfluxDB Details** vanno specificati i seguenti parametri:

- **Organization**: `home`
- **Token**: `<READ-ONLY-API-TOKEN>`
- **Default bucket**: `raw_data`

Premere il pulsante **Save & test** per verificare che la connessione è funzionante.

#### Grafana sulla porta 80

Le [istruzioni ufficiali](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#http_port):

> The port to bind to, defaults to 3000. To use port 80 you need to either give the Grafana binary permission for example:
>
>     $ sudo setcap 'cap_net_bind_service=+ep' /usr/sbin/grafana-server

l'istruzione `setcap` ha l'effetto di impedire l'avvio del server, probabilmente a causa di qualche permesso di accesso. Il file di log non viene aggiornato e per questa ragione risulta difficile risalire alla causa (Tra l'altro l'eseguibile associato al servizio risulta essere **/usr/share/grafana/bin/grafana** e non quello indicato nell'esempio).

L'alternativa suggerita, ovvero di installare e configurare **nginx** come *reverse-proxy* si è rivelata funzionante. Le istruzioni originali sono riportate in [Run Grafana behind a reverse proxy](https://grafana.com/tutorials/run-grafana-behind-a-proxy/):

- configurare il nome di dominio nella sezione `server` del file di configurazione **/etc/grafana/grafana.ini** di **grafana**:

        [server]
        # The public facing domain name used to access grafana from a browser
        domain = <raspberry-pi-IP>

- riavviare il servizio **grafana-server**:

        pi@raspberrypi:~ $ sudo systemctl restart grafana-server

- installare **nginx**:

        pi@raspberrypi:~ $ sudo apt install nginx

- configurare **nginx** copiando il seguente contenuto nel file **/etc/nginx/sites-enabled/grafana.conf**:

        # This is required to proxy Grafana Live WebSocket connections.
        map $http_upgrade $connection_upgrade {
          default upgrade;
          '' close;
        }
        
        upstream grafana {
          server localhost:3000;
        }
        
        server {
          listen 80;
          root /usr/share/nginx/html;
          index index.html index.htm;
        
          location / {
            proxy_set_header Host $host;
            proxy_pass http://grafana;
          }
        
          # Proxy Grafana Live WebSocket connections.
          location /api/live/ {
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
            proxy_pass http://grafana;
          }
        }

- eliminare il link simbolico **/etc/nginx/sites-enabled/default**:

        pi@raspberrypi:~ $ sudo rm /etc/nginx/sites-enabled/default

- riavviare il servizio **nginx**:

        pi@raspberrypi:~ $ sudo systemctl restart nginx

- configurare l'avvio automatico del servizio **nginx**:

        pi@raspberrypi:~ $ sudo systemctl enable nginx

### Solarmon

Installare i sorgenti del servizio clonandoli da Git:

    pi@raspberry:~ $ git clone https://github.com/gzuliani/solarmon.git

Modificare il file **main.py** definendo gli opportuni insiemi di dispositivi di ingresso e uscita.

Creare un *virtual env* nella cartella principale di Solarmon:

    pi@raspberrypi:~/solarmon $ python -m venv venv

Attivare l'ambiente virtuale ed installare le dipendenze via `pip`:

    pi@raspberrypi:~/solarmon $ . venv/bin/activate
    (venv) pi@raspberrypi:~/solarmon $ pip3 install requests==2.32.3
    (venv) pi@raspberrypi:~/solarmon $ pip3 install pymodbus==3.9.2

La libreria **pymodbus** non è particolarmente stabile. Solarmon è stato collaudato sulle versioni 3.0.0.rc1, 3.6.3, 3.6.4 e 3.9.2.

Seguire le [apposite istruzioni](https://github.com/gzuliani/solarmon/blob/main/debian/lib/systemd/system/readme.md) per registrare l'applicativo come servizio.

#### Strategie iniziali

L'acquisizione dei parametri principali avverrà ogni 30s; i campioni saranno salvati nel bucket **raw_data** che avrà una *data retention* limitata, non superiore all'anno.

Un *task* si occuperà di aggregare quotidianamente i dati dei flussi energetici(1) nel bucket dedicato **daily_data**. Dato l'interesse e il limitato impatto che questi dati hanno sull'occupazione disco, questi saranno conservati indefinitamente. Attenzione: la schedulazione del task è espressa in UTC: se il task è programmato per la mezzanotte, di fatto verrà eseguito all'una di notte durante l'ora solare, alle due quando vige l'ora legale.

Non è stata ancora definita una politica di backup; avrebbe senso effettuarne uno con frequenza almeno doppia rispetto al *data retention* più breve.

(1) Per flussi energetici si intende l'energia che durante il giorno è transitata da/per i vari componenti dell'impianto, quindi:

- energia generata dai pannelli
- energia da/per la batteria
- energia da/per la griglia
- energia richiesta dai carichi
- energia in uscita dall'inverter
- energia in entrata nell'inverter

Poiché gran parte di queste grandezze sono espresse con valori con segno, bisognerà fare attenzione ad integrare separatamente le componenti positive e quelle negative. Si consideri ad esempio il parametro `battery_power` dell'inverter che esprime la potenza in uscita dalla batteria: un valore negativo indica che questa è in fase di carica. Alla luce di ciò l'energia erogata dalla batteria durante il giorno corrisponderà all'integrale nel tempo della funzione `max(0, battery_power)`, mentre per quella introdotta si userà la funzione `max(0, -battery_power)`.

### Dataplicity

[Dataplicity](https://dataplicity.com/) è un servizio di remotizzazione del terminale della Raspberry Pi. Offre inoltre la possibilità di pubblicare in rete un server web installato in locale (cfr. "[Host a website from your Pi](https://docs.dataplicity.com/docs/host-a-website-from-your-pi)").

L'installazione è gratuita per una singola scheda. La procedura è descritta nella pagina [Installation procedure](https://docs.dataplicity.com/docs/getting-started-with-dataplicity#installation-procedure).

#### Errore "Device not connected"

Se il portale di Dataplicity mostra l'errore "Device not connected" la ragione spesso è la perdita della rete WiFi da parte della Raspberry Pi. A volte però è accaduto che la scheda risultasse raggiungibile attraverso rete locale. In tali situazioni è stato risolutivo il riavvio del servizio **tuxtunnel**:

    pi@raspberrypi:~ $ sudo supervisorctl restart tuxtunnel
    tuxtunnel: stopped
    tuxtunnel: started

Alcuni spunti su come migliorare l'affidabilità del servizio sono riportati nella pagina [Improving reliability](https://docs.dataplicity.com/docs/improving-reliability).

## Appendice A - Note su InfluxDB

### Note generali

- i tempi vanno sempre espressi in coordinate UTC (specificare la timezone `Z` nelle query);
- il raggruppamento settimanale inizia il giovedì (1/1/1970 era un giovedì); usare l'offset per portarlo a lunedì(4)/domenica(3), per esempio con l'operatore `time(1w, 4d)`;
- per ottenere l'elenco dei tag di un bucket:
        show tag keys from "..."
        show field keys from "..."
- non è possibile inserire in un `field` un valore di tipo diverso di quello del campo stesso
- il tipo di un campo viene determinato all'atto del primo inserimento e non può essere modificato successivamente
- una query influx produce un insieme di tabelle (concetto di "flusso" di tabelle):
  > If coming from relational SQL or SQL-like query languages, such as InfluxQL, the data model that Flux uses is different than what you’re used to. Flux returns multiple tables where each table contains a different field. A “relational” schema structures each field as a column in each row.
  Fonte: [Flux data model](https://docs.influxdata.com/flux/v0.x/get-started/data-model/).
  Inoltre:
  > By default, from() returns data queried from InfluxDB grouped by series (measurement, tags, and field key). Each table in the returned stream of tables represents a group. Each table contains the same values for the columns that data is grouped by. This grouping is important as you aggregate data.
- `pivot` unifica un flusso di tabelle in un'unica tabella, di norma sul tempo; operazione necessaria per valorizzare campi calcolati;
- `experimental.unpivot` trasforma una tabella in un flusso di tabelle, operazione necessaria per smembrare una tabella in un flusso di tabelle dopo aver definito e valorizzato le colonne calcolate;
- il parametro `timeSrc` in `aggregateWindow` specifica il dato orario da associare l'aggregato calcolato nell'intervallo specificato;
- nei predicati sono ammessi solo gli operatori uguaglianza (=) e congiunzione (AND);
- l'operatore `contains`, sebbene più compatto, è molto meno efficiente di una sequenza di `if` (fino a 10 volte tanto):

        fields = ["f1", "f2", "f3"]
        |> filter(fn: (r) => contains(value:r["_field"], set:fields))

  è molto più lenta di:

        |> filter(fn: (r) => r["_field"] == "f1" or r["_field"] == "f2" or r["_field"] == "f3")
- `math.mMax` e `math.mMin` sono molto meno efficienti di un `if`:

        math.mMax(x: r["f1"], y: 0.)

  è molto più lenta di

    if r["f1"] > 0. then r["f1"] else 0.

- poiché la "data retention" caratterizza un bucket, dati con "data retention" diversi devono finire in bucket diversi;
- Errore "Out of Memory" durante le query su grosse moli di dati:
  > Through some digging was able to decipher that the “out of memory” was due to the indexing being in memory “inmem” (log files from docker) and simply using up all available RAM. Turns out that the “inmem” is the default influxdb.conf file setting for index-version = “inmem” parameter. After further reading, found that one remedy to this issue was to set the index-version = “tsi1” parameter in the influxdb.conf file so that indexing uses disk rather than RAM.
  Fonte: [Fatal error: Out of Memory](https://community.influxdata.com/t/fatal-error-out-of-memory/16103).

### Importazione CSV

Esempio di importazione di un file CSV prodotto da **solarmon**:

    pi@raspberry:~ $ influx write dryrun \
        -b raw_data \
        -f data.csv \
        --header "#constant measurement,solarmon" \
        --header "#constant tag,source,inverter" \
        --header "#datatype dateTime:RFC3339Nano,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double,double"

### Esportazione CSV

    pi@raspberry:~ $ influx query 'from(bucket:"raw_data") |> range(start: 2023-09-25T22:00:00Z, stop: 2023-09-27T20:00:00Z) |> filter(fn: (r) => r["source"] == "inverter")' --raw > out.csv

### Cancellazione dei dati

    pi@raspberry:~ $ influx delete \
        --bucket raw_data \
        --predicate '_measurement="solarmon" AND source="meter-1"' \
        --start '2023-01-01T00:00:00Z' \
        --stop '2024-01-01T00:00:00Z'

    pi@raspberry:~ $ influx delete \
        --bucket daily_data \
        --predicate '_measurement="solarmon"' \
        --start '2022-01-01T00:00:00Z' \
        --stop '2024-01-01T00:00:00Z'

**Nota**: il comando `delete` non supporta l'operatore logico `NOT` né i filtri su `_field`. L'API **/api/v2/delete** invece non soffre di queste limitazioni.

### Spazio occupato su disco

    pi@raspberry:~ $ sudo -i
    root@raspberrypi:~# cd /var/lib/influxdb/engine/data/
    root@raspberrypi:/var/lib/influxdb/engine/data# du -sh ./*

### Backup

> Back up data with the influx CLI
>
> #### Syntax
>
>     influx backup <backup-path> -t <root-token>
>
> #### Example
>
>     influx backup \
>       path/to/backup_$(date '+%Y-%m-%d_%H-%M') \
>       -t xXXXX0xXX0xxX0xx_x0XxXxXXXxxXX0XXX0XXxXxX0XxxxXX0Xx0xx==
>
Fonte: [Back up data](https://docs.influxdata.com/influxdb/v2/admin/backup-restore/backup/)

Predisposto il seguente script di backup **backup.sh**:

    #!/bin/bash

    INFLUX=/usr/local/bin/influx
    BASE_DIR=/home/pi/solarmon/influxdb/backup
    mkdir -p $BASE_DIR
    BACKUP_DIR=$BASE_DIR/$(date '+%Y%m%d%H%M')
    echo Creating InfluxDB backup $BACKUP_DIR...
    $INFLUX backup $BACKUP_DIR -t <ROOT-TOKEN>
    tar -zcvpf $BACKUP_DIR.tar.gz $BACKUP_DIR
    rm -rf $BACKUP_DIR

Schedularlo affinché venga effettuato alla mezzanotte del primo giorno di ogni mese:

    pi@raspberry:~ $ crontab -e

aggiungere quindi la riga:

    0 0 1 * * /home/pi/solarmon/influxdb/backup.sh 2>&1 | /usr/bin/logger -t cron --rfc5424=inotq,notime,nohost

### Restore

> Restore to a new InfluxDB server
>
> If using a backup to populate a new InfluxDB server:
>
> - Retrieve the admin token from your source InfluxDB instance.
>
> - Set up your new InfluxDB instance, but use the -t, --token flag to use the admin token from your source instance as the admin token on your new instance.
>
>       influx setup --token My5uP3rSecR37t0keN
>
> - Restore the backup to the new server.
>
>       influx restore \
>         /backups/2020-01-20_12-00/ \
>         --full
>
>If you do not provide the admin token from your source InfluxDB instance as the admin token in your new instance, the restore process and all subsequent attempts to authenticate with the new server will fail.

Fonte: [Restore data](https://docs.influxdata.com/influxdb/v2/admin/backup-restore/restore/).

Verificato il buon funzionamento su un'istanza diversa di InfluxDB installata su una Raspberry Pi 3B.

### Ripristino della serie storica "raw_data"

L'installazione InfluxDB a bordo della Raspberry Pi sulla quale gira il servizio Solarmon contiene due bucket:

- **raw_data** che contiene i dati orari (campionati ogni secondo);
- **daily_data** che contiene gli aggregati giornalieri.

Per limitare il consumo di spazio sulla SD card il primo bucket ha una *data retention* di un anno, il secondo infinita.

Il backup del contenuto del database avviene ogni tre mesi.

Come ricostruire l'intera serie temporale a partire dai backup periodici?

#### Creazione dell'istanza InfluxDB

Considerate le limitate risorse della Raspberry Pi conviene effettuare il ripristino su una macchina più carrozzata. Dopo aver proceduto all'installazione di una versione di InfluxDB compatibile con quello d'origine, recuperare il token amministrativo dell'istanza InfluxDB della Raspberry Pi e creare una nuova istanza sulla macchina di destinazione identica all'originale, avendo quindi cura di fornire gli stessi nome utente, organizzazione e bucket. L'unica differenza sta nela data retention del il bucket "raw_data", che in questo caso sarà illimitata:

    user@host:~$ influx setup --token [ROOT-TOKEN]
    > Welcome to InfluxDB 2.0!
    ? Please type your primary username pi
    ? Please type your password ************
    ? Please type your password again ************
    ? Please type your primary organization name home
    ? Please type your primary bucket name raw_data
    ? Please type your retention period in hours, or 0 for infinite 0
    ? Setup with these parameters?
      Username:          pi
      Organization:      home
      Bucket:            raw_data
      Retention Period:  infinite
    Yes
    User    Organization    Bucket
    pi      home            raw_data

#### Ripristino di backup precedenti l'ultimo

Poiché il backup più recente contiene l'intera serie temporale del bucket "daily_data", non è necessario importarlo dai backup precedenti; è perciò sufficiente recuperare i dati del bucket "raw_data". Poiché il ripristino di un bucket distrugge la sua versione in linea, occorre procedere in due fasi:

- recuperare i dati del bucket "raw_data" dal backup ripristinandoli in un bucket temporaneo;
- riversare i dati dal bucket temporaneo nel bucket "raw_data".

I comandi sono:

    user@host:~$ influx restore BACKUP-DIR --bucket raw_data --new-bucket raw_data_tmp
    user@host:~$ influx query 'from(bucket:"raw_data_tmp") |> range(start: START-TIME, stop: END-TIME) |> to(bucket: "raw_data")' > /dev/null
    user@host:~$ influx bucket delete -n raw_data_tmp

I parametri START-TIME ed END-TIME possono essere prefissati (es. START-TIME alla data di messa in opera del sistema di monitoraggio, END-TIME la data odierna) oppure determinati dalla data del backup (es. fintanto che la data retention del bucket "raw_data" è pari a un anno: START-TIME = BACKUP-TIME - 365d, END-TIME=BACKUP-TIME)

**Nota**: considerato che il bucket "raw_data" contiene i dati orari di un anno e che i backup vengono effettuati con cadenza trimestrale, per velocizzare il processo di ripristino conviene procedere rispettando la sequenza temporale dei backup iniziando dal più remoto; dei successivi sarà sufficiente estrarre i soli dati relativi agli ultimi mesi.

#### Ripristino del backup più recente

Nell'ipotesi che l'istanza di InfluxDB sia aggiornata al penultimo backup, l'integrazione dei dati dell'ultimo deve considerare anche il bucket "daily_data":

    user@host:~$ influx restore BACKUP-DIR --bucket raw_data --new-bucket raw_data_tmp
    user@host:~$ influx query 'from(bucket:"raw_data_tmp") |> range(start: START-TIME, stop: END-TIME) |> to(bucket: "raw_data")' > /dev/null
    user@host:~$ influx bucket delete -n raw_data_tmp

    user@host:~$ influx bucket delete -n daily_data
    user@host:~$ influx restore BACKUP-DIR --bucket daily_data

#### Export CSV

Sono almeno due le strade percorribili per salvare i dati grezzi e gli aggregati giornalieri anno per anno su file CSV:

- esportazione su CSV annotato (formato proprietario)

        user@host:~$ influx query 'from(bucket:"raw_data") |> range(start:2024-01-01T00:00:00Z, stop:2025-01-01T00:00:00Z) |>drop (columns:["_start", "_stop", "_measurement"])' --raw > raw_data_2024.txt

  Lo svantaggio principale è la dimensione del file ottenuto, dovuta alla verbosità del formato: oltre 2.8GB.

- esportazione tabulare

        user@host:~$ influx query 'from(bucket: "raw_data") |> range(start: 2024-01-01T00:00:00Z, stop: 2025-01-01T00:00:00Z) |> filter(fn: (r) => r.source=="inverter") |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") |> drop(columns: ["_start", "_stop", "_measurement", "source"])' --raw > inverter_2024.txt

  Lo svantaggio in questo caso è l'impossibilità di esportare i dati in un'unica soluzione: l'operazione `pivot` richiede un quantitativo eccessivo di memoria per gli 8GB di RAM di cui è dotato il portatile in uso. L'alternativa è separare i dati per sorgente; l'esportazione in questo caso ha successo e complessivamente ammonta a 512MB:

  | Sorgente  | Dimensione |
  |-----------|-----------:|
  | 2nd-floor |     91.2MB |
  | air-cond  |     80.1MB |
  | gnd-floor |     93.0MB |
  | inverter  |    164.8MB |
  | osmer     |    414.7kB |
  | program   |      2.2MB |
  | rasp      |     80.9MB |

  L'esportazione tabulare inoltre è applicabile anche agli aggregati giornalieri:

        user@host:~$ influx query 'from(bucket: "daily_data") |> range(start: 2024-01-01T00:00:00Z, stop: 2025-01-01T00:00:00Z)|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") |> drop(columns: ["_start", "_stop", "_measurement"])' --raw > daily_data_2024.txt

  Il file risultante pesa 74.8kB.

### Task di aggregazione giornaliero

Definito il task `daily_aggregates` e schedulato alle ore 02:00 UTC con un offset di 5 minuti. La versione iniziale del task (in assenza di contatori di energia dedicati al controllo dei consumi di specifici dispositivi):

    import "date"
    import "experimental"
    import "math"

    option task = {name: "daily_aggregates", cron: "0 2 * * *", offset: 5m}

    yesterdayStart = date.truncate(t: date.sub(d: 1d, from: now()), unit: 1d)
    yesterdayStop = date.add(d: 1d, to: yesterdayStart)

    from(bucket: "raw_data")
      |> range(start: yesterdayStart, stop: yesterdayStop)
      |> filter(fn: (r) => r["_measurement"] == "solarmon")
      |> filter(fn: (r) =>
          (r["source"] == "inverter"
              and (r["_field"] == "battery_power"
              or r["_field"] == "pv1_power"
              or r["_field"] == "pv2_power"
              or r["_field"] == "inverter_power"
              or r["_field"] == "load_power"
              or r["_field"] == "grid_power"))
          or (r["_field"] == "active-power"
              and (r["source"] == "gnd-floor"
              or r["source"] == "2nd-floor"
              or r["source"] == "air-cond"
              or r["source"] == "ind-plane")),)
      |> pivot(rowKey: ["_time"], columnKey: ["source", "_field"], valueColumn: "_value")
      |> map(fn: (r) => ({r with "gnd-floor_in": r["gnd-floor_active-power"]}))
      |> map(fn: (r) => ({r with "2nd-floor_in": r["2nd-floor_active-power"]}))
      |> map(fn: (r) => ({r with "air-cond_in": r["air-cond_active-power"]}))
      |> map(fn: (r) => ({r with "ind-plane_in": r["ind-plane_active-power"]}))
      |> map(fn: (r) => ({r with "pv_out": r["inverter_pv1_power"] + r["inverter_pv2_power"]}))
      |> map(fn: (r) => ({r with "battery_out":
          if r["inverter_battery_power"] > 0 then
              r["inverter_battery_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "battery_in":
          if r["inverter_battery_power"] < 0 then
              -r["inverter_battery_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "grid_in":
          if r["inverter_grid_power"] > 0 then
              r["inverter_grid_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "grid_out":
          if r["inverter_grid_power"] < 0 then
              -r["inverter_grid_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "inverter_in":
          if r["inverter_inverter_power"] < 0 then
              -r["inverter_inverter_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "inverter_out":
          if r["inverter_grid_power"] > 0 then
              r["inverter_grid_power"]
          else
              0.,}),)
      |> map(fn: (r) => ({r with "load_in": r["inverter_load_power"]}))
      |> drop(columns: [
          "gnd-floor_active-power",
          "2nd-floor_active-power",
          "air-cond_active-power",
          "ind-plane_active-power",
          "inverter_battery_power",
          "inverter_grid_power",
          "inverter_inverter_power",
          "inverter_load_power",
          "inverter_pv1_power",
          "inverter_pv2_power",],)
      |> experimental.unpivot()
      |> aggregateWindow(
          every: 1d,
          fn: (column, tables=<-) => tables |> integral(unit: 1h),
          timeSrc: "_start",
          createEmpty: false,)
      |> to(bucket: "daily_data")

### Determinazione degli intervalli senza campioni

La query per la determinazione gli intervalli di tempo privi di campioni è la seguente:

    partial_data =
        from(bucket: "raw_data")
            |> range(start: START_OF_DAY, stop: START_OF_DAY + 1d)
            |> filter(fn: (r) => r["_measurement"] == "solarmon")
            |> filter(fn: (r) => r["source"] == "inverter" and r["_field"] == "run_state")
            |> aggregateWindow(every: 5m, fn: last, timeSrc: "_start")
            |> filter(fn: (r) => r["_value"] > 0)
            |> aggregateWindow(every: 1d, fn: count, timeSrc: "_start")
            |> map(fn: (r) => ({r with _value: 1440 - r._value * 5, _field: "no_data"}))
            |> drop(columns: ["source"])

ed è così strutturata:

- estrapolazione dei campioni di un registro arbitrario, in questo caso **run_state**, nel periodo considerato;
- suddivisione del periodo in intervalli di 5 minuti (con selezione dell'ultimo campione di ogni finestra temporale);
- selezione degli intervalli contenenti almeno un campione;
- conteggio del numero di tail intervalli nella giornata;
- conversione del conteggio in minuti (moltiplicazione per cinque) e determinazione della frazione giornaliera non coperta da campioni (1440 è il numero di minuti nella giornata).

La rimozione della colonna `source` avviene per uniformità con il task `daily_aggregates` che effettua un `pivot` che la rimuove implicitamente.

In questo modo si ottiene una buona stima della durata dei periodi di inattività del sistema, per quanto arrotondati ai 5 minuti sia in testa che in coda.

Il task giornaliero che alimenta il campo `no_data` che contiene il numero di minuti durante i quali non sono stati acquisiti campioni nella giornata precedente è così definito:

    import "array"
    import "date"

    option task = { name: "daily_missing_data", cron: "0 2 * * *", offset: 5m }

    yesterdayStart = date.truncate(t: date.sub(d: 1d, from: now()), unit: 1d)
    yesterdayStop = date.add(d: 1d, to: yesterdayStart)

    partial_data =
        from(bucket: "raw_data")
            |> range(start: yesterdayStart, stop: yesterdayStop)
            |> filter(fn: (r) => r["_measurement"] == "solarmon")
            |> filter(fn: (r) => r["source"] == "inverter" and r["_field"] == "run_state")
            |> aggregateWindow(every: 5m, fn: last, timeSrc: "_start")
            |> filter(fn: (r) => r["_value"] > 0)
            |> aggregateWindow(every: 1d, fn: count, timeSrc: "_start")
            |> map(fn: (r) => ({r with _value: 1440 - r._value * 5, _field: "no_data"}))
            |> drop(columns: ["source"])

    no_data =
        array.from(
            rows: [{_measurement: "solarmon", _field: "no_data", _value: 1440, _time: yesterdayStart}],
        )

    union(tables: [partial_data, no_data])
        |> group()
        |> min()
        |> to(bucket: "daily_data")

`partial_data` è l'interrogazione discussa prima; `no_data` è una query ausiliaria che ritorna invariabilmente il valore 1440 che rappresenta un'intera giornata priva di campioni; il task registra il minimo dei valori ottenuti. Lo strategemma si rende necessario perché a fronte di un'intera a giornata priva di campioni, `partial_data` produce un flusso vuoto anziché un flusso composto da una tabella vuota.

## Appendice B - Note su Grafana

- minimizzare il numero di interrogazioni condividendo il risultato di una query su più visualizzazioni diverse;
- nascondere una traccia per mezzo della proprietà "Hide in area";
- definire il nome di una traccia per mezzo della proprietà "Display name";
- differenziare il colore di una traccia per mezzo della proprietà "Threshold":
  > If the Color scheme is set to From thresholds (by value) and Gradient mode is set to Scheme, then the line or bar color changes as they cross the defined thresholds.
- definire il formato più adatto per i tempi sull'asse x per mezzo della proprietà "Unit" del campo "Time" (cfr. [Display](https://momentjs.com/docs/#/displaying/), applicabile solo ai grafici a barre).

## Appendice C - Note sull'inverter

L'inverter installato è un Deye SUN-6K-SG03LP1-EU. Si tratta di un inverter monofase ibrido, a doppio MPPT, per batterie a basso voltaggio. "Ibrido" indica il fatto che è in grado stoccare l'energia in eccesso prodotta dai pannelli fotovoltaici in un sistema di batterie, in questo caso a basso voltaggio (40÷60V). "A doppio MPPT" indica che l'inverter è dotato di due regolatori di carica di tipo MPPT, consente quindi il collegamento di due stringhe indipendenti di pannelli. MPPT (Maximum Power Point Tracker) si riferisce al regolatore di carica, che in alternativa può essere PWM. Rispetto a questo il regolatore MPPT è più complesso, costa di più, ma è più efficiente (20/30% circa).

### Punti di attenzione

- la potenza in uscita dalla batteria è limitata: usare carichi pesanti nottetempo potrebbe causare la richiesta di energia dalla rete (con i costi del caso);
- l'autoconsumo in caso di interruzione di energia elettrica non è automatico: in tale evenienza l'inverter si scollega dalla rete (e quindi dall'impianto) per fornire energia all'uscita "backup" (la commutazione è automatica e pressoché istantanea), sempre se ci sono carichi collegati a tale linea.

### Stima dei consumi

Con l'installazione dei contatori di energia a monte dei due quadri elettrici di casa dispongo di tre stime diverse dei consumi. Posto:

- **`battery_in`** l'integrale del valore assoluto della parte negativa di `battery_power`;
- **`battery_out`** l'integrale della parte positiva di `battery_power`;
- **`grid_id`** l'integrale della parte positiva di `grid_power`;
- **`grid_out`** l'integrale del valore assoluto della parte negativa di `grid_power`;
- **`pv_out`** la somma `pv1_power` e `pv2_power`;
- **`load_in`** il valore di `load_power`;
- **`house_in`** la somma delle potenze rilevate dai due contatori di energia;

e definendo:

- **`total_consumption`**:

        (pv_out - battery_in - grid_out) + battery_out + grid_in

  ove il primo termine rappresenta la porzione di energia fotovoltaica dirottata sul carico (formula equivalente: `pv1_power + pv2_power + battery_power + grid_power`);

- **`inverter_consumption`**:

        (pv_out - battery_in + battery_out) - inverter_power

  ove il primo termine rappresenta la potenza in ingresso all'inverter (DC), il secondo quella in uscita (AC). La formula può essere riscritta nella forma `pv1_power + pv2_power + battery_power - inverter_power`;

riscontro innazitutto che i valori di **`total_consumption`** sono allineati a quelli riportati dall'App SOLARMAN Smart, quindi che:

        total_consumption = load_in + inverter_consumption

La corrispondenza è totale, fino alle unità di W:

| day        | total_consumption | load_in | inverter_consumption |
|------------|------------------:|--------:|---------------------:|
| 2024-02-12 |            10.558 |   8.806 |                1.752 |
| 2024-02-13 |            11.131 |   9.207 |                1.925 |
| 2024-02-14 |            12.328 |  10.318 |                2.010 |
| 2024-02-15 |            10.390 |   8.266 |                2.124 |
| 2024-02-16 |            11.467 |   9.308 |                2.159 |
| 2024-02-17 |            11.341 |   9.259 |                2.082 |
| 2024-02-18 |            12.209 |  10.197 |                2.012 |
| 2024-02-19 |             9.595 |   7.641 |                1.955 |
| 2024-02-20 |            11.300 |   9.135 |                2.165 |
| 2024-02-21 |            11.119 |   8.931 |                2.188 |
| 2024-02-22 |             8.454 |   6.518 |                1.936 |
| 2024-02-23 |             8.599 |   6.917 |                1.683 |
| 2024-02-24 |            12.202 |  10.161 |                2.042 |
| 2024-02-25 |            12.507 |  10.344 |                2.162 |
| 2024-02-26 |             9.570 |   7.395 |                2.175 |
| 2024-02-27 |             7.949 |   5.960 |                1.989 |
| 2024-02-28 |             9.509 |   7.479 |                2.031 |
| 2024-02-29 |             4.898 |   3.119 |                1.780 |

La spiegazione più naturale è che l'inverter determini il valore **`load_power`** con la formula:

        load_power = inverter_power + grid_power

Vale inoltre la relazione:

        total_consumption = load_in > house_in

### Anomalie

La documentazione dell'inverter riporta l'elenco delle possibili anomalie, identificate nella forma `Fxx`, ove `xx` è un codice numerico compreso tra `08` e `64` (cfr. sez. "7. Fault information and processing" della guida utente).

La specifica dell'interfaccia Modbus dell'inverter etichetta i registri 103, 104, 105 e 106 rispettivamente "Fault information word 1", "Fault information word 2", "Fault information word 3" e "Fault information word 4".

Il 7 marzo 2024 alle ore 14:15 l'applicazione SolarSMART ha registrato un'anomalia di tipo **F55DC_VoltHigh_Fault**. In quell'istante i valori dei quattro registri erano:

| Registro | Valore |
|:--------:|:------:|
|      103 |      0 |
|      104 |      0 |
|      105 |      0 |
|      106 |     64 |

Riscrivendo il tutto in formato binario:

    -------106------- -------105------- -------104------- -------103-------
    76543210 76543210 76543210 76543210 76543210 76543210 76543210 76543210

    00000000 01000000 00000000 00000000 00000000 00000000 00000000 00000000

L'unico bit a 1 è quello in posizione 54. Sembra quindi probabile che il codice delle anomalie presenti in un dato istante si ricavi sommando 1 all'indice dei bit a 1 del campo di bit ottenuto dalla giustapposizione dei 4 registri sopra indicati.

Sotto questa ipotesi, ecco una query che evidenzia le anomalie riscontrate nell'ultimo mese:

    import "bitwise"
    import "date"
    import "strings"

    pastMonthStart = date.truncate(t: date.sub(d: 30d, from: v.timeRangeStop), unit: 1d)

    from(bucket: "raw_data")
      |> range(start: pastMonthStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "solarmon" and r.source == "inverter" and r._field == "fault_code" and r._value > uint(v: 0))
      |> map(fn: (r) => ({r with b00: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v:  0))) > 0) then "F01" else ""}))
      |> map(fn: (r) => ({r with b06: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v:  6))) > 0) then "F07" else ""}))
      |> map(fn: (r) => ({r with b12: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 12))) > 0) then "F13" else ""}))
      |> map(fn: (r) => ({r with b14: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 14))) > 0) then "F15" else ""}))
      |> map(fn: (r) => ({r with b15: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 15))) > 0) then "F16" else ""}))
      |> map(fn: (r) => ({r with b17: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 17))) > 0) then "F18" else ""}))
      |> map(fn: (r) => ({r with b19: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 19))) > 0) then "F20" else ""}))
      |> map(fn: (r) => ({r with b20: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 20))) > 0) then "F21" else ""}))
      |> map(fn: (r) => ({r with b21: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 21))) > 0) then "F22" else ""}))
      |> map(fn: (r) => ({r with b22: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 22))) > 0) then "F23" else ""}))
      |> map(fn: (r) => ({r with b23: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 23))) > 0) then "F24" else ""}))
      |> map(fn: (r) => ({r with b25: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 25))) > 0) then "F26" else ""}))
      |> map(fn: (r) => ({r with b28: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 28))) > 0) then "F29" else ""}))
      |> map(fn: (r) => ({r with b33: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 33))) > 0) then "F34" else ""}))
      |> map(fn: (r) => ({r with b34: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 34))) > 0) then "F35" else ""}))
      |> map(fn: (r) => ({r with b40: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 40))) > 0) then "F41" else ""}))
      |> map(fn: (r) => ({r with b41: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 41))) > 0) then "F42" else ""}))
      |> map(fn: (r) => ({r with b45: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 45))) > 0) then "F46" else ""}))
      |> map(fn: (r) => ({r with b46: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 46))) > 0) then "F47" else ""}))
      |> map(fn: (r) => ({r with b47: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 47))) > 0) then "F48" else ""}))
      |> map(fn: (r) => ({r with b54: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 54))) > 0) then "F55" else ""}))
      |> map(fn: (r) => ({r with b55: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 55))) > 0) then "F56" else ""}))
      |> map(fn: (r) => ({r with b57: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 57))) > 0) then "F58" else ""}))
      |> map(fn: (r) => ({r with b61: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 61))) > 0) then "F62" else ""}))
      |> map(fn: (r) => ({r with b62: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 62))) > 0) then "F63" else ""}))
      |> map(fn: (r) => ({r with b63: if (bitwise.uand(a: r._value, b: bitwise.ulshift(a: uint(v: 1), b: uint(v: 63))) > 0) then "F64" else ""}))
      |> map(fn: (r) => ({r with fault_codes: strings.joinStr(arr: [r.b00, r.b06, r.b12, r.b14, r.b15, r.b17, r.b19, r.b20, r.b21, r.b22, r.b23, r.b25, r.b28, r.b33, r.b34, r.b40, r.b41, r.b45, r.b46, r.b47, r.b54, r.b55, r.b57, r.b61, r.b62, r.b63], v: " ")}))
      |> keep(columns: ["_time", "fault_codes"])

### `load_power` nullo

Accade a volte che il parametro `load_power` assuma il poco verosimile valore zero:

![`load_power` nullo](img/null_load_power.png)

Grazie all'installazione di due contatori di energia nei due quadri elettrici di casa posso verificare che si tratta di una discrepanza attribuibile all'inverter:

| time                | meter_1 | meter_2 | load_power |
|---------------------|---------|---------|------------|
| 2024-03-25T12:07:40 | 0.005   | 0.257   | 0.214      |
| 2024-03-25T12:08:10 | 0.005   | 0.040   | 0.183      |
| 2024-03-25T12:08:41 | 0.005   | 0.040   | 0.000      |
| 2024-03-25T12:09:11 | 0.005   | 0.249   | 0.030      |
| 2024-03-25T12:09:41 | 0.005   | 0.245   | 0.031      |
| 2024-03-25T12:10:12 | 0.006   | 0.040   | 0.078      |
| 2024-03-25T12:10:42 | 0.005   | 0.051   | 0.000      |
| 2024-03-25T12:11:12 | 0.005   | 0.048   | 0.030      |
| 2024-03-25T12:11:43 | 0.005   | 0.049   | 0.030      |
| 2024-03-25T12:12:13 | 0.005   | 0.043   | 0.031      |
| 2024-03-25T12:12:44 | 0.005   | 0.043   | 0.120      |
| 2024-03-25T12:13:14 | 0.005   | 0.194   | 0.000      |
| 2024-03-25T12:13:44 | 0.005   | 0.047   | 0.000      |
| 2024-03-25T12:14:15 | 0.005   | 0.052   | 2.180      |
| 2024-03-25T12:14:45 | 0.005   | 2.110   | 0.030      |
| 2024-03-25T12:15:16 | 0.005   | 2.060   | 0.030      |
| 2024-03-25T12:15:46 | 0.005   | 2.380   | 2.510      |
| 2024-03-25T12:16:16 | 0.005   | 2.430   | 2.550      |
| 2024-03-25T12:16:47 | 0.006   | 2.470   | 2.570      |

Può quindi accadere di vedere la linea del `load_power` scendere al di sotto della somma della potenza registrata dai due contatori di energia:

![`load_power` inferiore alla potenza assorbita dai carichi](img/inconsistent_load_power_level.png)

La ragione è che quei sporadici ed inattesi valori nulli del `load_power` causano un temporaneo abbassamento della media mobile mostrata nei grafici.

## Appendice D - Passaggio dall'ora legale a quella solare

InfluxDB aggrega i dati sulla base dei tempi UTC. Grafana mostra invece i dati nell'orario locale:

![Passaggio ora legale/ora solare la notte del 29/10/2023](img/grafana_dst.png)

Quando InfluxDB aggrega i dati orari in quelli giornalieri, cosa accade dei dati raccolti nell'ora aggiuntiva introdotta dal passaggio all'ora legale? Nulla: gli aggregati determinati da InfluxDB coprono sempre e comunque 24 ore, perché è solo nell'orario locale che la durata della giornata del 29/10/2023 è di 25 ore:

![Passaggio ora legale/ora solare in UTC e nell'orario locale](img/utc_vs_local_dst.png)

## Appendice E - Acquisizione dati dall'OsmerFVG

L'Osservatorio meteorologico regionale consente di scaricare i dati orari e gli aggregati giornalieri acquisiti dalle varie stazioni di cui dispone alla pagina [https://dev.meteo.fvg.it/](https://dev.meteo.fvg.it/). I dati orari vengono resi disponibili dopo il ventesimo minuto dell'ora successiva (i dati relativi all'intervallo temporale 11:00÷12:00 sono pubblicati alle 12:20).

**Nota 1**: non è corretto estrarre i massimi/minimi di giornata dai dati orari, essendo questi delle medie orarie. Se di interesse, scaricare quelli giornalieri a fine giornata direttamente dal sito. L'unica eccezione è il valore di radiazione che, essendo un integrale, quello giornaliero equivale alla somma degli integrali orari.

**Nota 2**: il bollettino delle 00:20 è vuoto; pensavo contenesse i dati dell'intervallo 23:00÷00:00 della giornata precedente, ma evidentemente non è così. La perdita del dato di radiazione non influisce molto sui computi giornalieri, se non per qualche unità.

**[Aggiornamento del 17/04/2024]** Ricevo il seguente messaggio dall'OsmerFVG in risposta alla mia segnalazione fatta un paio di settimane fa:

>> Buongiorno,
>>
>> scrivo per un chiarimento.
>>
>> Ho da poco installato un impianto solare e sto sviluppando in
>> autonomia un piccolo sistema di monitoraggio dell'impianto. Volendo
>> incrociare i valori della potenza erogata dai pannelli con
>> l'irraggiamento ho predisposto un componente software che scarica i
>> dati orari della stazione "UDI" dal vostro sito all'URL
>> "https://dev.meteo.fvg.it/xml/stazioni/UDI.xml".
>>
>> Mi sono accorto che registro sistematicamente l'assenza del dato
>> nell'acquisizione delle 00:30. Ho inteso che dopo il ventesimo minuto
>> di ogni ora voi rendete disponibili i dati dell'ora precedente, motivo
>> per cui mi sarei atteso di trovare i dati relativi all'intervallo
>> orario 23:00-00:00 della giornata precedente.
>>
>> Perdere quel campione non cambia nulla per i miei scopi, ma volevo
>> essere sicuro di non sbagliare qualcosa.
>>
>> In particolare, vedo che il nodo `meteo_data`, oltre all'anagrafica
>> della stazione, contiene solo il dato di `cloudiness`.
>>
>> [omissis]
>
> Buongiorno Sig. Zuliani,
>
> grazie della segnalazione, dovremmo aver risolto il problema da lei riscontrato.
>
> A disposizione per eventuali chiarimenti

Il problema è effettivamente rientrato.

**Nota 3**: riferendosi all'ora precedente a quella di acquisizione, i dati provenienti da questa sorgente vanno traslati indietro di un'ora prima di essere messi a confronto con i dati acquisiti in tempo reale:

    radiation = from(bucket: "raw_data")
    |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
    |> filter(fn: (r) => r._measurement == "solarmon")
    |> filter(fn: (r) => (r.source == "osmer" and r._field == "radiation"))
    |> timeShift(duration: -1h)
    |> drop(columns: ["_measurement", "source"])

    pv_power = from(bucket: "raw_data")
    |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
    |> filter(fn: (r) => r._measurement == "solarmon")
    |> filter(fn: (r) =>
        (r.source == "inverter" and r._field == "pv1_power")
        or (r.source == "inverter" and r._field == "pv2_power"))
    |> drop(columns: ["_measurement", "source"])

    union(tables: [radiation, pv_power])

Se non si effettua l'operazione `timeShift` i dati risultano essere fuori sincrono:

![Ritardo dei dati meteorologici rispetto a quelli acquisiti in tempo reale](img/out_of_sync_radiation.png)

## Appendice F - Esempio di query "complessa"

Esempio di sviluppo di una query "complessa", in questo caso l'aggregato settimanale dei consumi giornalieri ripartiti per sorgente. Si presuppone che il campo `pv_out` indichi l'energia prodotta dai pannelli, `battery_out` quella erogata dalla batteria, `grid_in` quella acquistata dalla rete. In prima approssimazione la quota d'energia dei pannelli direttamente utilizzata dai carichi si determina scorporando da `pv_out` la parte immagazzinata nella batteria (`battery_in`) e quella rilasciata in rete (`grid_out`):

    import"date"
    import "experimental"
    import "math"

    todayStart = date.truncate(t: now(), unit: 1d)
    todayStop = now()

    pastWeekStart = date.truncate(t: date.sub(d: 6d, from: now()), unit: 1d)
    pastWeekStop = date.truncate(t: now(), unit: 1d)

    pastWeek = from(bucket: "daily_data")
    |> range(start: pastWeekStart, stop: pastWeekStop)
    |> filter(fn: (r) => r["_measurement"] == "solarmon")
    |> filter(fn: (r) =>
        r["_field"] == "pv_out"
        or r["_field"] == "battery_in"
        or r["_field"] == "battery_out"
        or r["_field"] == "grid_in"
        or r["_field"] == "grid_out")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> map(fn: (r) => ({r with "used": r["pv_out"] - r["battery_in"] - r["grid_out"]}))
    |> drop(columns: ["pv_out", "battery_in", "grid_out"])
    |> experimental.unpivot()

`range` seleziona i dati giornalieri dell'ultima settimana; le clausole `filter` selezionano i dati di interesse; il risultato è un flusso di 5 tabelle, una per ogni serie:

| Time                | pv_out      |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        2.63 |
| 2024-01-01 01:00:00 |        9.10 |
| 2024-01-02 01:00:00 |       11.00 |
| 2024-01-03 01:00:00 |        4.05 |
| 2024-01-04 01:00:00 |        5.50 |
| 2024-01-05 01:00:00 |        6.48 |

| Time                | battery_in  |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        1.10 |
| 2024-01-01 01:00:00 |        6.41 |
| 2024-01-02 01:00:00 |        7.38 |
| 2024-01-03 01:00:00 |        0.97 |
| 2024-01-04 01:00:00 |        3.46 |
| 2024-01-05 01:00:00 |        3.61 |

| Time                | battery_out |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        0.66 |
| 2024-01-01 01:00:00 |        5.04 |
| 2024-01-02 01:00:00 |        3.40 |
| 2024-01-03 01:00:00 |        3.61 |
| 2024-01-04 01:00:00 |        2.12 |
| 2024-01-05 01:00:00 |        2.86 |

| Time                | grid_in     |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        8.11 |
| 2024-01-01 01:00:00 |        3.41 |
| 2024-01-02 01:00:00 |        3.14 |
| 2024-01-03 01:00:00 |        5.17 |
| 2024-01-04 01:00:00 |        7.02 |
| 2024-01-05 01:00:00 |        4.97 |

| Time                | grid_out    |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        0.00 |
| 2024-01-01 01:00:00 |        0.01 |
| 2024-01-02 01:00:00 |        0.02 |
| 2024-01-03 01:00:00 |        0.02 |
| 2024-01-04 01:00:00 |        0.01 |
| 2024-01-05 01:00:00 |        0.00 |

`pivot` raggruppa le tabelle utilizzando il tempo come chiave:

| Time                | pv_out | battery_in | battery_out | grid_in | grid_out |
|---------------------|--------|------------|-------------|---------|----------|
| 2023-12-31 01:00:00 |   2.63 |       1.10 |        0.66 |    8.11 |     0.00 |
| 2024-01-01 01:00:00 |   9.10 |       6.41 |        5.04 |    3.41 |     0.01 |
| 2024-01-02 01:00:00 |  11.00 |       7.38 |        3.40 |    3.14 |     0.02 |
| 2024-01-03 01:00:00 |   4.05 |       1.00 |        3.61 |    5.17 |     0.02 |
| 2024-01-04 01:00:00 |   5.50 |       3.46 |        2.12 |    7.02 |     0.01 |
| 2024-01-05 01:00:00 |   6.48 |       3.61 |        2.86 |    4.97 |     0.00 |

La funzione `map` calcola il nuovo campo "used":

| Time                | pv_out | battery_in | battery_out | grid_in | grid_out | used |
|---------------------|--------|------------|-------------|---------|----------|------|
| 2023-12-31 01:00:00 |   2.63 |       1.10 |        0.66 |    8.11 |     0.00 | 1.53 |
| 2024-01-01 01:00:00 |   9.10 |       6.41 |        5.04 |    3.41 |     0.01 | 2.69 |
| 2024-01-02 01:00:00 |  11.00 |       7.38 |        3.40 |    3.14 |     0.02 | 3.65 |
| 2024-01-03 01:00:00 |   4.05 |       1.00 |        3.61 |    5.17 |     0.02 | 3.06 |
| 2024-01-04 01:00:00 |   5.50 |       3.46 |        2.12 |    7.02 |     0.01 | 2.03 |
| 2024-01-05 01:00:00 |   6.48 |       3.61 |        2.86 |    4.97 |     0.00 | 2.87 |

La funzione `drop` cancella le colonne non più necessarie:

| Time                | battery_out | grid_in | used |
|---------------------|-------------|---------|------|
| 2023-12-31 01:00:00 |        0.66 |    8.11 | 1.53 |
| 2024-01-01 01:00:00 |        5.04 |    3.41 | 2.69 |
| 2024-01-02 01:00:00 |        3.40 |    3.14 | 3.65 |
| 2024-01-03 01:00:00 |        3.61 |    5.17 | 3.06 |
| 2024-01-04 01:00:00 |        2.12 |    7.02 | 2.03 |
| 2024-01-05 01:00:00 |        2.86 |    4.97 | 2.87 |

Infine, la funzione `unpivot` separa le singole colonne in altrettante tabelle producendo così la serie seguente:

| Time                | battery_out |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        0.66 |
| 2024-01-01 01:00:00 |        5.04 |
| 2024-01-02 01:00:00 |        3.40 |
| 2024-01-03 01:00:00 |        3.61 |
| 2024-01-04 01:00:00 |        2.12 |
| 2024-01-05 01:00:00 |        2.86 |

| Time                | grid_in     |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        8.11 |
| 2024-01-01 01:00:00 |        3.41 |
| 2024-01-02 01:00:00 |        3.14 |
| 2024-01-03 01:00:00 |        5.17 |
| 2024-01-04 01:00:00 |        7.02 |
| 2024-01-05 01:00:00 |        4.97 |

| Time                | used        |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        1.53 |
| 2024-01-01 01:00:00 |        2.69 |
| 2024-01-02 01:00:00 |        3.65 |
| 2024-01-03 01:00:00 |        3.06 |
| 2024-01-04 01:00:00 |        2.03 |
| 2024-01-05 01:00:00 |        2.87 |

Ognuna delle tabelle della serie dà origine ad una traccia indipendente in Grafana.

Questi dati possono essere integrati con il cumulativo parziale della giornata in corso:

    today = from(bucket: "raw_data")
    |> range(start: todayStart, stop: todayStop)
    |> filter(fn: (r) => r["_measurement"] == "solarmon")
    |> filter(fn: (r) =>
        ((r["source"] == "inverter") and (
        r["_field"] == "battery_power"
        or r["_field"] == "pv1_power"
        or r["_field"] == "pv2_power"
        or r["_field"] == "grid_power")))
    |> pivot(rowKey: ["_time"], columnKey: ["source", "_field"], valueColumn: "_value")
    |> map(fn: (r) => ({r with "battery_in":
        if r["inverter_battery_power"] < 0 then -r["inverter_battery_power"] else 0.}))
    |> map(fn: (r) => ({r with "battery_out":
        if r["inverter_battery_power"] > 0 then r["inverter_battery_power"] else 0.}))
    |> map(fn: (r) => ({r with "grid_in":
        if r["inverter_grid_power"] > 0 then r["inverter_grid_power"] else 0.}))
    |> map(fn: (r) => ({r with "grid_out":
        if r["inverter_grid_power"] < 0 then -r["inverter_grid_power"] else 0.}))
    |> map(fn: (r) => (
        {r with "used":
            r["inverter_pv1_power"] + r["inverter_pv2_power"] - r["battery_in"] - r["grid_out"]
        }))
    |> drop(columns: ["inverter_battery_power", "inverter_grid_power", "inverter_pv1_power", "inverter_pv2_power", "inverter_load_power", "pv_out", "battery_in", "grid_out"])
    |> experimental.unpivot()
    |> aggregateWindow(every: 1d, fn: (column, tables=<-) => tables |> integral(unit:1h), timeSrc: "_start", createEmpty: false)

La logica è analoga alla query precedente; l'unica differenza sta nel passo finale di integrazione oraria (le energie sono tutte espresse in Wh) per mezzo della funzione `aggregateWindow`:

| Time                | battery_out |
|---------------------|-------------|
| 2024-01-06 01:00:00 |        0.21 |

| Time                | grid_in     |
|---------------------|-------------|
| 2024-01-06 01:00:00 |        7.40 |

| Time                | used        |
|---------------------|-------------|
| 2024-01-06 01:00:00 |        0.39 |

Le due query ora vanno unificate per ottenere un'unica serie di tre tabelle:

    union(tables: [pastWeek, today])
    |> group()
    |> drop(columns: ["_start", "_stop", "_measurement"])
    |> group(columns: ["_field"])

| Time                | battery_out |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        0.66 |
| 2024-01-01 01:00:00 |        5.04 |
| 2024-01-02 01:00:00 |        3.40 |
| 2024-01-03 01:00:00 |        3.61 |
| 2024-01-04 01:00:00 |        2.12 |
| 2024-01-05 01:00:00 |        2.86 |
| 2024-01-06 01:00:00 |        0.21 |

| Time                | grid_in     |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        8.11 |
| 2024-01-01 01:00:00 |        3.41 |
| 2024-01-02 01:00:00 |        3.14 |
| 2024-01-03 01:00:00 |        5.17 |
| 2024-01-04 01:00:00 |        7.02 |
| 2024-01-05 01:00:00 |        4.97 |
| 2024-01-06 01:00:00 |        7.40 |

| Time                | used        |
|---------------------|-------------|
| 2023-12-31 01:00:00 |        1.53 |
| 2024-01-01 01:00:00 |        2.69 |
| 2024-01-02 01:00:00 |        3.65 |
| 2024-01-03 01:00:00 |        3.06 |
| 2024-01-04 01:00:00 |        2.03 |
| 2024-01-05 01:00:00 |        2.87 |
| 2024-01-06 01:00:00 |        0.39 |

Da notare la direttiva `drop()` che, eliminando le colonne di sistema `_start` e `_stop`, consente il raggruppamento dei dati giornalieri per nome del parametro.

## Appendice G - Stabilizzazione della connessione WiFi

Di tanto in tanto la Raspberry Pi 4 perde la connessione alla rete WiFi e non la riaggancia più. L'unica soluzione a quel punto è forzare il riavvio della scheda scollegando l'alimentazione per qualche secondo. In rete sono molteplici gli articoli che suggeriscono di disattivare il Power Management del modulo WiFi e il protocollo IPv6 nella speranza di rendere la connessione più stabile.

### Disabilitare il Power Management del modulo WiFi

Verificare che il Power Management è attivo:

    pi@raspberrypi:~ $ iwconfig
    ...

    wlan0     IEEE 802.11  ESSID:********
              Mode:Managed  Frequency:5.26 GHz  Access Point: 00:00:00:00:00:00
              Bit Rate=292.5 Mb/s   Tx-Power=31 dBm
              Retry short limit:7   RTS thr:off   Fragment thr:off
        >>>>  Power Management:on
              Link Quality=37/70  Signal level=-73 dBm
              Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
              Tx excessive retries:49  Invalid misc:0   Missed beacon:0

Aprire il file `/etc/rc.local` e aggiungere la riga:

    /sbin/iwconfig wlan0 power off

Riavviare la scheda, quindi verificare che il Power Management non è più attivo:

    pi@raspberrypi:~ $ iwconfig
    ...

    wlan0     IEEE 802.11  ESSID:********
              Mode:Managed  Frequency:5.26 GHz  Access Point: 00:00:00:00:00:00
              Bit Rate=292.5 Mb/s   Tx-Power=31 dBm
              Retry short limit:7   RTS thr:off   Fragment thr:off
        >>>>  Power Management:off
              Link Quality=37/70  Signal level=-73 dBm
              Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
              Tx excessive retries:49  Invalid misc:0   Missed beacon:0

### Disabilitare il protocollo IPv6

Di norma il protocollo IPv6 è abilitato:

    pi@raspberrypi:~ $ ifconfig
    ...

    wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            inet 192.168.1.184  netmask 255.255.255.0  broadcast 192.168.1.255
      >>>>  inet6 fe80::fc5e:d7e3:c16:6b88  prefixlen 64  scopeid 0x20<link>
            ether d8:3a:dd:4b:aa:58  txqueuelen 1000  (Ethernet)
            RX packets 8052  bytes 3113138 (2.9 MiB)
            RX errors 0  dropped 1  overruns 0  frame 0
            TX packets 26465  bytes 24747264 (23.6 MiB)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

Per disabilitare il protocollo IPv6 aprire il file `/etc/sysctl.conf` e aggiugere la riga:

    net.ipv6.conf.all.disable_ipv6 = 1

Rendere effettiva la nuova impostazione con il comando:

    pi@raspberrypi:~ $ sudo sysctl -p

Verificare che il protocollo IPv6 non è più in uso:

    pi@raspberrypi:~ $ ifconfig
    ...

    wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            inet 192.168.1.184  netmask 255.255.255.0  broadcast 192.168.1.255
            ether d8:3a:dd:4b:aa:58  txqueuelen 1000  (Ethernet)
            RX packets 8931  bytes 3218531 (3.0 MiB)
            RX errors 0  dropped 1  overruns 0  frame 0
            TX packets 27069  bytes 24824989 (23.6 MiB)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

Per riattivare il protocollo IPv6 cancellare la riga o impostare il parametro a `0`, quindi ridare il comando `sudo sysctl -p`.

### Riavviare il sistema

Esistono diverse soluzioni in rete. Tra le più recenti c'è lo script `wifi-check` realizzato da [Chris Dzombak](https://github.com/cdzombak/dotfiles/blob/master/linux/pi/wifi-check.sh) (novembre 2023). Istruzioni complete alla pagina [Maintaining a solid WiFi connection on Raspberry Pi](https://www.dzombak.com/blog/2023/12/Maintaining-a-solid-WiFi-connection-on-Raspberry-Pi.html).

Lo script (disponibile in locale [qui](../../../debian/usr/local/bin/wifi-check.sh)) va copiato nella cartella **/usr/local/bin** e reso eseguibile con il comando:

    pi@raspberrypi:~ $ chmod +x /usr/local/bin/wifi-check.sh

Ho deciso di schedulare lo script (disponibile in locale [qui](../../../debian/usr/local/bin/wifi-check.sh)) ogni 5 minuti. Per far ciò ho creato il file `/etc/cron.d/wifi-check` contenente la seguente riga:

    */5 * * * * root flock -x -n -E 0 /tmp/wifi-check.lock env PING_TARGET=192.168.1.1 WLAN_IF=wlan0 /usr/local/bin/wifi-check.sh

L'analisi del log può essere effettuata attraverso il comando:

    pi@raspberry:~ $ journalctl -t wifi-check.sh

eventualmente corredato di uno o più filtri temporali (cfr. ad esempio flag `-S --since`, `-U --until`).

## Appendice H - Ripristino del sistema in seguito al guasto della scheda SD

**Per ripristinare l'istanza InfluxDB è indispensabile disporre del token amministrativo originale!**

Si procede con la preparazione del sistema come da istruzioni, con l'avvertenza di **saltare il passaggio "[Configurazione di InfluxDB](#configurazione-di-influxdb)"**. Quindi:

- copiare l'immagine del sistema operativo Raspberry Pi OS sulla scheda SD ricordandosi di attivare il servizio **ssh**;
- configurare e stabilizzare la connessione WiFi:
  - disattivando il Power Management;
  - disattivando il protocollo IPv6;
  - installando e schedulando lo script **wifi-check.sh**.
- configurare il modulo RTC;
- configurare l'adattatore USB/RS485;
- installare InfluxDB;
- installare Grafana;
- installare nginx;
- installare Solarmon;
- installare Dataplicity.

Si procede quindi con il ripristino dei backup del database InfluxDB e dei pannelli di Grafana.

### Ripristino dell'ultimo backup di InfluxDB

Procedere da terminale con il comando:

    pi@raspberrypi:~$ influx setup --token [ROOT-TOKEN]
    > Welcome to InfluxDB 2.0!
    ? Please type your primary username pi
    ? Please type your password ********
    ? Please type your password again ********
    ? Please type your primary organization name home
    ? Please type your primary bucket name raw_data
    ? Please type your retention period in hours, or 0 for infinite 8760
    ? Setup with these parameters?
      Username:          pi
      Organization:      home
      Bucket:            raw_data
      Retention Period:  8760h0m0s
     Yes
    User    Organization    Bucket
    pi  home        raw_data

I dati immessi devono coincidere con quelli forniti in origine.

Dopo aver copiato l'ultimo backup disponibile sulla scheda e averlo scompattato, si può procedere con il ripristino:

    pi@raspberrypi:~$ influx restore [BACKUP-FOLDER] --full

A questo punto si può schedulare il backup periodico come già descritto in precedenza.

### Ripristino dell'ultimo backup di Grafana

Arrestare il servizio **grafana-server** con il comando:

    pi@raspberrypi:~$ sudo systemctl stop grafana-server

Sostituire il file `/var/lib/grafana/grafana.db` con l'ultima versione disponibile, quindi riavviare il servizio:

    pi@raspberrypi:~$ sudo systemctl start grafana-server

Avviare infine il servizio **solarmon**.

È conveniente caricare i dati giornalieri (assegnando loro il valore 0) per il periodo non coperto dal backup: la presenza di valori nulli rende i diagrammi prodotti da Grafana di più facile interpretazione rispetto a quando questi sono assenti. Il programma Python sottostante produce il codice in formato *line protocol* a risoluzione di 1 secondo adatto per essere caricato direttamente dall'interfaccia utente di InfluxDB:

    from datetime import datetime, timedelta, timezone

    measurement = 'solarmon'
    fields = [
        'gnd-floor_in',
        '2nd-floor_in',
        'air-cond_in',
        'ind-plane_in',
        'pv_out',
        'battery_out',
        'battery_in',
        'grid_in',
        'grid_out',
        'inverter_in',
        'inverter_out',
        'load_in',
    ]
    
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    while start_date < end_date:
        start_date += timedelta(days=1)
        for field in fields:
            print(f'{measurement} {field}=0 {int(start_date.timestamp())}')
