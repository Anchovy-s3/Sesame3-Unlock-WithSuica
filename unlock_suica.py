# -*- coding: utf-8 -*-
import requests
import json
import binascii
import nfc
import time
import datetime, base64, requests, json
from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from threading import Thread, Timer
import sys
import io

#Sesame Unlock Script
uuid = {'UUID'} #下にももう一箇所
secret_key = {'secret_key'}
api_key = {'api_key'}

cmd = 88  # 88/82/83 = toggle/lock/unlock
history = 'unlock with suica'
base64_history = base64.b64encode(bytes(history, 'utf-8')).decode()

print(base64_history)
headers = {'x-api-key': api_key}
cmac = CMAC.new(bytes.fromhex(secret_key), ciphermod=AES)

ts = int(datetime.datetime.now().timestamp())
message = ts.to_bytes(4, byteorder='little')
message = message.hex()[2:8]
cmac = CMAC.new(bytes.fromhex(secret_key), ciphermod=AES)

cmac.update(bytes.fromhex(message))
sign = cmac.hexdigest()

# Suica待ち受けの1サイクル秒
TIME_cycle = 1.0
# Suica待ち受けの反応インターバル秒
TIME_interval = 0.2
# タッチされてから次の待ち受けを開始するまで無効化する秒
TIME_wait = 3

# NFC接続リクエストのための準備
# 212F(FeliCa)で設定
target_req_suica = nfc.clf.RemoteTarget("212F")
# 0003(Suica)
target_req_suica.sensf_req = bytearray.fromhex("0000030000")

print ('Waiting for SUICA...')
while True:
    # USBに接続されたNFCリーダに接続してインスタンス化
    clf = nfc.ContactlessFrontend('usb')
    # Suica待ち受け開始
    # clf.sense( [リモートターゲット], [検索回数], [検索の間隔] )
    target_res = clf.sense(target_req_suica, iterations=int(TIME_cycle//TIME_interval)+1 , interval=TIME_interval)
    
    if not target_res is None:
        
        tag = nfc.tag.activate_tt3(clf, target_res)
        tag.sys = 3
        
        #IDmを取り出す
        idm = binascii.hexlify(tag.idm)
        idmd = idm
        print ('Suica detected. idm = ' + idm.decode())

        #文字列IOストリームを初期化してfに代入
        with io.StringIO() as f:
            sys.stdout = f

            print(idm.decode())
            read_idm = f.getvalue()
            sys.stdout = sys.__stdout__

        idm1 = '01390dcb2787e6f5'    #iPhone12 Pro
        idm2 = '0140e078e037b660'    #Pixel5
        idm3 = '01392b161487e6f5'    #Apple Watch Serise 4
        if (idm1 in read_idm) or (idm2 in read_idm) or (idm3 in read_idm) :

            # 鍵の操作
            url = f'https://app.candyhouse.co/api/sesame2/{UUID}/cmd'  #UUIDをここにも
            body = {
                'cmd': cmd,
                'history': base64_history,
                'sign': sign
            }
            res = requests.post(url, json.dumps(body), headers=headers)
            print(res.status_code, res.text)
            print ("sleep " + str(TIME_wait) + " seconds")
            time.sleep(TIME_wait)
    #end if
    
    clf.close()

#end while