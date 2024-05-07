This example demonstrates an issue with gate.io websocket streams.

briefly, the issue is that when the download speed of client’s internet channel is slower than the amount of data gate trying to push, websocket updates become corrupted.

To illustrate the issue we created a small test example which subscribes to all order books (for all spot trading pairs). 

I should point again that in a real situation the bot\terminal may be subscribed to much less data and still meet the issue, this example subscribes to that much data only in order to illustrate the issue !

Steps to reproduce:
Run the test example for long enough. 
If the amount of data sent by the exchange is greater than the bandwidth of your channel, you will notice that the Latency value in the application increases.

Then soon there will be an error in the next push:

ERROR cannot decode: b'{"time":1714869315,"time_ms":1714869315382,"channel":"spot.order_book_update","event":"update","result":{"t":1714869315288,"e":"depthUpdate","E":1714869315,"s":"LQTY_USDT","U":1184735236,\x81~\x01\x07{"time":1714869315,"time_ms":1714869315530,"channel":"spot.order_book_update","e'

The message is corrupted, its truncated and contains some unreadable chars


According to our observations, corrupted messages always contain byte sequence 
hex 81 7E
(which seems to be messed control opcode of two or more frames).
