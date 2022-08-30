# -*- coding: utf-8 -*-
from starlette.middleware.cors import CORSMiddleware
import multiprocessing
import logging
import os
import time
import wave
from multiprocessing import set_start_method
from detect_noise import noise_detector
from multiprocessing.queues import Queue
from typing import Optional
from scipy.io.wavfile import read, write
import numpy as np
import math
import io

import uvicorn
from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import errno  



app = FastAPI()
list_tone = []

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
root = os.path.dirname(__file__)

app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')

templates = Jinja2Templates(directory=os.path.join(root, 'template'))
             
                
def change_to_mathfloor(num):
    return math.floor(num*10)/10
    
def conv_to_int(num):
    if (num >= 1.0):
        new = 32767
    elif (num <= -1.0):
        new = -32768
    else:
        new = num * 32768.0
    return int(new)
    
def monotone():
    global list_tone
    new_list = [change_to_mathfloor(tone) for tone in list_tone]
    small_change = 0
    big_change = 0
    high = 0
    low = 0
    good = 0
    for i in range(2,len(list_tone)-1):
        
        if round(new_list[i+1] - new_list[i],1) in [0.1,-0.1]:
            small_change += 1
        if round(new_list[i+1] - new_list[i],1) <= -0.2 or round(new_list[i+1] - new_list[i],1) >= 0.2:
            big_change += 1
        if new_list[i] >= 0.4:
            high += 1
        elif new_list[i] <= 0.1:
            low += 1
        else:
            good += 1
    
    return small_change, high, low, good,big_change
 
    
def result_tone():
    global list_tone
    small_change, high, low, good, big_change = monotone()
    if good < 0.5*(len(list_tone)-3) and small_change <= 0.5*(len(list_tone)-2):
        return "#"*80+"\n" +" "*40+"Results:\n Apathetic Tone\n"
    if good >= 0.5*(len(list_tone)-3) and small_change+big_change >= 0.3*(len(list_tone)-2):
        return "#"*80+"\n" +" "*40+"Results:\n That was good\n"
    if high >= 0.5*(len(list_tone)-3):
        return "#"*80+"\n"+" "*40+"Results:\n High voice\n"
    if low >= 0.5*(len(list_tone)-3):
        return "#"*80+"\n"+" "*40+"Results:\n Low voice\n"

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
    
def wav_worker(q: Queue, uid: str, ):
    root = os.path.join(os.path.dirname(__file__), 'upload_waves')
    os.makedirs(root, exist_ok=True)
    filename = os.path.join(root, f'{uid}_{time.time()}.wav')
    try:
        wav = wave.open(filename, mode='wb')
        wav.setframerate(16000)
        wav.setnchannels(1)
        wav.setsampwidth(2)

        while True:
            data_bytes = q.get()
            wav.writeframes(data_bytes)
            print(f'q.get {len(data_bytes)}')

    except Exception as e:
        logging.debug(e)
    finally:
        wav.close()

    logging.info('leave wav_worker')


@app.websocket("/items/{item_id}/ws")
async def websocket_signal_process(websocket: WebSocket, item_id: str, q: Optional[int] = None):
    global list_tone
    await websocket.accept()
    logging.info('websocket.accept')
    #while True:
    #    data = await websocket.receive_text()
    #    await websocket.send_text(f"Message text was: {data}")
    
    #ctx = multiprocessing.get_context()
    #queue = ctx.Queue()
    #process = ctx.Process(target=wav_worker, args=(queue, item_id))
    #process.start()
    counter = 0
    start1 = time.time()
    start2 = time.time()
    arr = []
    #arr_int = []
    message = ""
    message2 = ""
    try:
        while True:
            
            data = await websocket.receive()
            end1 = time.time()
            end2 = time.time()
            time_spent1 = end1 - start1
            time_spent2 = end2 - start2
            #print(time_spent1)
            # take a string of floats and convert it to list of floats '1.22,1.33' ==> ['1.33','1.233']
            data_array = data['text'].split(',')
            
            # convert the array items from string to floats ['1.33','1.233'] ==> [1.33,1.233]
            data_array = list(map(float, data_array))
            arr.extend(data_array)
            #arr_int.extend([conv_to_int(num) for num in data_array])
      
            if int(time_spent1) == 2:
                print("2 seconds passed")
                start1 = end1
                maxElement = max(arr)
                list_tone.append(maxElement)
                message = noise_detector(arr,16000)
                arr = []
                print(list_tone)
            
                await websocket.send_text(message)
            if int(time_spent2) == 30:
                start2 = end2
                #speech_feature_detector(arr_int)
                #arr_int = []
                message2 = result_tone()
                await websocket.send_text(message2)
                list_tone = []
            if q is not None:
                await websocket.send_text(f"Query parameter q is: {q}")
            #await websocket.send_text(f"Message text was: {data_array}, for item ID: {item_id}")
            
            #queue.put(data_array)
            counter += 1

    except Exception as e:
        logging.debug(e)
    #finally:
        # Wait for the worker to finish
        
        #queue.close()
        #queue.join_thread()
        # use terminate so the while True loop in process will exit
        #process.terminate()
        #process.join()
    logging.info('leave websocket_endpoint')
    
if __name__ == '__main__':
    # When using spawn you should guard the part that launches the job in if __name__ == '__main__':.
    # `set_start_method` should also go there, and everything will run fine.
    try:
        set_start_method('spawn')
    except RuntimeError as e:
        print(e)

    uvicorn.run('main:app', host='localhost',  reload=True)
