# Most common errors

## laura

    2023-01-22T13:57:01 WARNING Error "wrong size for frame b'CAN ERROR' (got 9, expected 14)" while reading parameter "T-mandata-CR"...
    2023-01-23T23:09:34 ERROR Could not write to "EmonCMS", reason: HTTPConnectionPool(host='127.0.0.1', port=80): Max retries exceeded with url: /input/post.json (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xb59d5470>: Failed to establish a new connection: [Errno 111] Connection refused'))
    2023-01-29T21:52:17 WARNING Error "wrong size for frame b'NO DATA' (got 7, expected 14)" while reading parameter "Pompa-percentuale"...
    2023-02-06T14:01:27 ERROR Could not read from "house", reason: Modbus Error: [Input/Output] No Response received from the remote unit/Unable to decode response
    2023-02-06T14:03:12 WARNING Cleanup recv buffer before send: 0xff
    2023-02-06T14:03:26 WARNING Cleanup recv buffer before send: 0xff 0xff 0xff 0xff 0xff 0xff

## andrea

    2023-01-30T16:11:59 WARNING Cleanup recv buffer before send: 0xff
    2023-01-31T07:09:44 WARNING Error "wrong size for frame b'CAN ERROR' (got 9, expected 14)" while reading parameter "Valvola-B1"...
    2023-01-31T22:07:42 WARNING Error "write failed: [Errno 5] Input/output error" while reading parameter "T-mandata-CR-SET"...
    2023-02-02T17:15:31 ERROR Could not write to "EmonCMS", reason: HTTPConnectionPool(host='127.0.0.1', port=80): Max retries exceeded with url: /input/post.json (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xb5a20710>: Failed to establish a new connection: [Errno 111] Connection refused'))
    2023-02-02T17:08:38 WARNING Error "wrong size for frame b'NO DATA' (got 7, expected 14)" whil
    2023-02-07T17:09:34 ERROR Could not read from "house", reason: Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 2 bytes (0 received)

Last update: 20230207
