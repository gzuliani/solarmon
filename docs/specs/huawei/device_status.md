# SUN2000 Device status

Registry address: 32089.

| Hex    | Dec   | Description                                                            |
|-------:|------:|:-----------------------------------------------------------------------|
| 0x0000 |     0 | Standby: initializing                                                  |
| 0x0001 |     1 | Standby: detecting insulation resistance                               |
| 0x0002 |     2 | Standby: detecting irradiation                                         |
| 0x0003 |     3 | Standby: drid detecting                                                |
| 0x0100 |   256 | Starting                                                               |
| 0x0200 |   512 | On-grid (Off-grid mode: running)                                       |
| 0x0201 |   513 | Grid connection: power limited (Off-grid mode: running: power limited) |
| 0x0202 |   514 | Grid connection: self-derating (Off-grid mode: running: self-derating) |
| 0x0203 |   515 | Off-grid Running                                                       |
| 0x0300 |   768 | Shutdown: fault                                                        |
| 0x0301 |   769 | Shutdown: command                                                      |
| 0x0302 |   770 | Shutdown: OVGR                                                         |
| 0x0303 |   771 | Shutdown: communication disconnected                                   |
| 0x0304 |   772 | Shutdown: power limited                                                |
| 0x0305 |   773 | Shutdown: manual startup required                                      |
| 0x0306 |   774 | Shutdown: DC switches disconnected                                     |
| 0x0307 |   775 | Shutdown: rapid cutoff                                                 |
| 0x0308 |   776 | Shutdown: input underpower                                             |
| 0x0401 |  1025 | Grid scheduling: cosφ-P curve                                          |
| 0x0402 |  1026 | Grid scheduling: Q-U curve                                             |
| 0x0403 |  1027 | Grid scheduling: PF-U curve                                            |
| 0x0404 |  1028 | Grid scheduling: dry contact                                           |
| 0x0405 |  1029 | Grid scheduling: Q-P curve                                             |
| 0x0500 |  1280 | Spot-check ready                                                       |
| 0x0501 |  1281 | Spot-checking                                                          |
| 0x0600 |  1536 | Inspecting                                                             |
| 0X0700 |  1792 | AFCI self check                                                        |
| 0X0800 |  2048 | I-V scanning                                                           |
| 0X0900 |  2304 | DC input detection                                                     |
| 0X0A00 |  2560 | Running: off-grid charging                                             |
| 0xA000 | 40960 | Standby: no irradiation                                                |
