# Solarmon

Note sul monitoraggio di termostati RF Honeywell.

## 20230205

Primi riferimenti:

* [Honeywell Evohome Monitoring](https://community.openenergymonitor.org/t/honeywell-evohome-monitoring/19906/7)
* [Script for feeding Honeywell Evohome data into Emoncms](https://community.openenergymonitor.org/t/script-for-feeding-honeywell-evohome-data-into-emoncms/1342)
* [Honeywell CH/DHW via RF - evohome, sundial, hometronics, chronotherm](https://community.home-assistant.io/t/honeywell-ch-dhw-via-rf-evohome-sundial-hometronics-chronotherm/151584)

## 20230225

[RAMSES II](https://github.com/zxdavb/ramses_protocol) dovrebbe essere il nome del protocollo utilizzato dal termostato Honeywell; la libreria [ramses_rf](https://github.com/zxdavb/ramses_rf) è quella generalmente utilizzata per interfacciarsi con dispositivi che fanno uso di questo protocollo. Fortunatamente, la libreria è scritta in Python, quindi non dovrebbe essere troppo complicato integrarla in Solarmon.

## 20230226

RAMSES II è un protocollo binario che viaggia su RF a 868MHz. Esistono degli adattatori RF/USB che intercettano i pacchetti che viaggiano su radio frequenza e li presentano su connessione seriale. Honeywell HGI80 è la soluzione ufficiale, costosa e di difficile reperibilità; esistono molte alternative, diverse delle quali open source.

Nano CUL 868 è l'adattatore attualmente in lizza. Ma è compatibile con la libreria **ramses_rf**? In teoria dovrebbe esserlo, una volta che sull'adattatore sia stato caricato il firmware [evofw3](https://github.com/ghoti57/evofw3). [Qui](https://gathering-tweakers-net.translate.goog/forum/list_messages/2164770?_x_tr_sl=auto&_x_tr_tl=it&_x_tr_hl=it&_x_tr_pto=wapp) le istruzioni per fare il flash del firmware.

Alcuni venditori offrono la possibilità di scegliere il firmware con cui ricevere il dispositivo (es.[nanoCUL 868](https://schlauhaus.biz/en/product/nanocul-868/)), altri lo propongono direttamente in versione evofw3 (es. [SSM-D2](https://indalo-tech.onlineweb.shop/SSM-D2/p7844707_21584696.aspx)).

## 20230319

Scovata un'implementazione in C++ nel progetto [https://github.com/domoticz/domoticz](https://github.com/domoticz/domoticz); i sorgenti si trovano nella cartella `hardware`, nei file con prefisso `Evohome`.

Un progetto che usa la libreria `ramses_rf` è [evoGateway](https://github.com/smar000/evoGateway), può risultare utile come esempio di integrazione.

Informazioni dettagliate sul protocollo si trovano invece nel wiki del progetto [ramses_protocol](https://github.com/zxdavb/ramses_protocol/wiki).
