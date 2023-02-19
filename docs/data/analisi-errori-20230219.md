# Analisi errori

I log coprono il periodo che va dalle 16 dell'11/02/2023 alle 21 del 19/02/2023.

## Andrea

### Errori

866 errori, così suddivisi:

* 540 errori di comunicazione con il contatore "house"
* 324 errori di comunicazione con il contatore "old-pv"

I restanti due sono:

    2023-02-12T17:34:17 WARNING Error "wrong size for frame b'3210FA01D601A8<RX ERROR' (got 23, expected 14)" while reading parameter "T-ACS"...
    2023-02-12T22:17:52 ERROR Could not write to "EmonCMS", reason: HTTPConnectionPool(host='127.0.0.1', port=80): Max retries exceeded with url: /input/post.json (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xb5a431b0>: Failed to establish a new connection: [Errno 111] Connection refused'))

Gli errori rilevati sono così distribuiti nei giorni:

| Data       | Errori "house" | Errori "old-pv" | Note         |
|------------|----------------|-----------------|--------------|
| 11/02/2023 |             21 |              12 | dalle 16     |
| 12/02/2023 |             55 |              28 |              |
| 13/02/2023 |             77 |              34 |              |
| 14/02/2023 |             69 |              47 |              |
| 15/02/2023 |             73 |              42 |              |
| 16/02/2023 |             60 |              40 |              |
| 17/02/2023 |             71 |              41 |              |
| 18/02/2023 |             54 |              49 |              |
| 19/02/2023 |             59 |              30 | fino alle 21 |

### Warning

3505 segnalazioni registrate, tutte riconducibili alla comunicazione con la pompa di calore Daikin, di cui 3503 casi `NO DATA`. Le due altre segnalazioni sono:

    2023-02-12T07:57:42 WARNING Cleanup recv buffer before send: 0xff
    2023-02-12T17:34:17 WARNING Error "wrong size for frame b'3210FA01D601A8<RX ERROR' (got 23, expected 14)" while reading parameter "T-ACS"...

Va tenuto conto che della pompa di calore vengono rilevati 26 parametri e se si verifica un errore di lettura sul primo è assai probabile che lo stesso errore si verifichi anche per quelli successivi:

* 127 notifiche 'NO DATA` relative a "T-mandata", il primo parametro letto
* 153 notifiche 'NO DATA` relative a "T-mandata-CR", l'ultimo parametro letto

| Data       | Segnalazioni `NO DATA` | Note         |
|------------|------------------------|--------------|
| 11/02/2023 |                      9 | dalle 16     |
| 12/02/2023 |                     17 |              |
| 13/02/2023 |                     19 |              |
| 14/02/2023 |                     15 |              |
| 15/02/2023 |                     23 |              |
| 16/02/2023 |                     16 |              |
| 17/02/2023 |                     18 |              |
| 18/02/2023 |                     21 |              |
| 19/02/2023 |                     14 | fino alle 21 |

## Laura

### Errori

Solamente due errori registrati, entrambi relativi a EmonCMS:

    2023-02-12T16:56:35 ERROR Could not write to "EmonCMS", reason: HTTPConnectionPool(host='127.0.0.1', port=80): Max retries exceeded with url: /input/post.json (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xb5a773b0>: Failed to establish a new connection: [Errno 111] Connection refused'))
    2023-02-14T17:14:48 ERROR Could not write to "EmonCMS", reason: HTTPConnectionPool(host='127.0.0.1', port=80): Max retries exceeded with url: /input/post.json (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xb5a0d0d0>: Failed to establish a new connection: [Errno 111] Connection refused'))

### Warning

3184 segnalazioni, di cui 3183 relative ad errori `NO DATA`; la rimantente ha probabilmente a che fare con un tentativo di connessione diretto all'adattatore OBD mentre questo era già in uso dal servizio "solarmon":

    WARNING Error "wrong size for frame b'STOPPED' (got 7, expected 14)" while reading parameter "E-risc-BUH"...

La distribuzione nei giorni è analoga a quella della pompa di calore di Andrea:

| Data       | Segnalazioni `NO DATA` | Note         |
|------------|------------------------|--------------|
| 11/02/2023 |                      7 | dalle 16     |
| 12/02/2023 |                     20 |              |
| 13/02/2023 |                     19 |              |
| 14/02/2023 |                     20 |              |
| 15/02/2023 |                     21 |              |
| 16/02/2023 |                     16 |              |
| 17/02/2023 |                     22 |              |
| 18/02/2023 |                     22 |              |
| 19/02/2023 |                     18 | fino alle 21 |
