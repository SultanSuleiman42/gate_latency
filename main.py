import requests
import json
import hashlib
import hmac
import logging
import time
from time import sleep
import threading
import numpy as np
from websocket import WebSocketApp  
import sys

b = []

allPairs = []
allPairsSplit = []
 
log = []

counter = 0
latency = 0

time_ms = ''
currency_pair = ''
symbolList = [] 
 


logging.basicConfig(filename='logfile_GATE_latency.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


def currentTime():
    milliseconds = int(round(time.time() * 1000))
    return milliseconds
 

def getPairs():
    global allPairs,allPairsSplit 
    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    url = '/spot/tickers'
    r = requests.request('GET', host + prefix + url, headers=headers)
    r = json.loads(r.text)
    for i in r:
        if i['base_volume'] != '0':
            allPairs.append(i['currency_pair'])
    chunks = np.array_split(allPairs, len(allPairs) // 110)
    
    b = 0
    for i in chunks:
        allPairsSplit.append(chunks[b].tolist())
        b = b+1



class GateWebSocketApp(WebSocketApp):

    def __init__(self, url, api_key, api_secret,token_list, **kwargs):
        super(GateWebSocketApp, self).__init__(url, **kwargs)
        self._api_key = api_key
        self._api_secret = api_secret
        self._token_list = token_list

    # def _send_ping(self, interval, event):
    #     while not event.wait(interval):
    #         self.last_ping_tm = time.time()
    #         if self.sock:
    #             try:
    #                 self.sock.ping()
    #             except Exception as ex:
    #                 logging.warning("send_ping routine terminated: {}".format(ex))
    #                 break
    #             try:
    #                 self._request("spot.ping", auth_required=False)
    #             except Exception as e:
    #                 raise e

    def _request(self, channel, event=None, payload=None, auth_required=True):
        current_time = int(time.time())
        data = {
            "time": current_time,
            "channel": channel,
            "event": event,
            "payload": payload,
        }
        if auth_required:
            message = 'channel=%s&event=%s&time=%d' % (channel, event, current_time)
            data['auth'] = {
                "method": "api_key",
                "KEY": self._api_key,
                "SIGN": self.get_sign(message),
            }
        data = json.dumps(data)
        logging.info('request: %s', data)
        self.send(data)

    def get_sign(self, message):
        h = hmac.new(self._api_secret.encode("utf8"), message.encode("utf8"), hashlib.sha512)
        return h.hexdigest()

    def subscribe(self, channel, payload=None, auth_required=True):
        self._request(channel, "subscribe", payload, auth_required)

    def unsubscribe(self, channel, payload=None, auth_required=True):
        self._request(channel, "unsubscribe", payload, auth_required)


def on_message(ws, message):
    global messages,counter,latency,last_latency,log
    counter +=1

    messages = json.loads(message) 
    
    if messages.get('event') == 'subscribe':
        logging.info(f'subscribe on  {messages.get("payload")}')
        
    if messages.get("time"):
        last_latency = messages.get("time")
        latency = int(time.time() - messages.get("time"))
 
       
                
    if messages.get('event') == 'update':
        pass
    else:
        logging.info(messages) 
         
    
    
     
def on_error(wsapp, err):
    print("error encountered: ", err)
    logging.info("error encountered: ", err)
    
    
def on_open(ws):
    # type: (GateWebSocketApp) -> None
    # subscribe to channels interested
    logging.info('websocket connected')
     
    for tokena in allPairs: 
        # print(tokena)
        ws.send(json.dumps({
        "time": int(time.time()),
        "channel": "spot.order_book_update",
        "event": "subscribe",  # "unsubscribe" for unsubscription
        "payload": [tokena, "100ms"]
        }))
        time.sleep(0.01)
     
    
def on_close(ws, close_status_code, close_msg):
    print(f'[on_close] close_status_code={close_status_code} close_msg={close_msg}')


def latencyTheard():
    while True:
        sys.stdout.write('\r' + ' ' * 50 + '\r')  # Очищение строки
        sys.stdout.write(f'MsgCount [{counter}]. Latency = [{latency}]')
        sys.stdout.flush()       
        sleep(1)

def start(token_list):
    threading.Thread(target=latencyTheard,).start()
    
    app = GateWebSocketApp("wss://api.gateio.ws/ws/v4/",
                            "YOUR_API_KEY",
                            "YOUR_API_SECRET",
                            token_list=token_list,
                            on_open=on_open,
                            on_message=on_message,
                            on_close=on_close,
                            on_error=on_error)
    app.run_forever(ping_interval=5) 

  
getPairs()  
start(allPairsSplit)


