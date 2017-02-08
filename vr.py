#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import MFRC522
import time
import os
import glob
import shutil
import subprocess
import signal
import hashlib
import wave
from multiprocessing import Process
from collections import deque
import const

def GPIO_setup():
    '''
    Setup RFID reader and Gpio
    '''
    global MIFAREReader
    MIFAREReader = MFRC522.MFRC522()
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(const.SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(const.READY,GPIO.OUT)
    #GPIO.setup(const.SEND,GPIO.OUT)
    #GPIO.add_event_detect(const.SWITCH, GPIO.RISING, bouncetime = 250)

def P0():
    '''
    Working process
    Name, write files and send announce
    '''
    global sending

    print("Working process started")
    
    sending += 1
    # check file creation
    #if (not os.path.isfile(const.PATH_PICAM + "rec/*.ts")):
    if (not os.path.isfile(const.PATH_BASE + "out.h264")):
       print('no file')
       return
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    m.update(const.getserial() + str(int(time.mktime(time.strptime(timenow,"%Y-%m-%d %H:%M:%S"))))) #md5
    filename = m.hexdigest()

    #Write audio
    wf = wave.open(const.PATH_BASE + "out.wav", 'wb')

    waves = b''.join(audio_buffer)
    new_waves = [waves[i:i + 2] for i in range(0, len(waves) - 1, 4)]

    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(44100 // 2)
    wf.writeframes(b''.join(new_waves))
    wf.close()

    # time.sleep(3)
    # newest = max(glob.iglob(const.PATH_PICAM + 'rec/*.[Tt][Ss]'), key=os.path.getctime)
    subprocess.call("MP4Box -add out.wav -add " + const.PATH_BASE + "out.h264 " + const.PATH_SEND + "out.mp4", shell=True)
    os.rename(const.PATH_SEND + "out.mp4", const.PATH_SEND + filename + ".mp4")
    # os.rename(newest, const.PATH_SEND + filename + ".ts")
    # shutil.copy2(newest, const.PATH_SEND + filename + ".ts")
    # linkto = os.readlink(newest)
    # os.remove(const.PATH_PICAM + 'rec/' + linkto)
    # os.remove(newest)

    #Flush videofile
    # videofile = open(const.PATH_SEND + filename + ".ts","r")
    videofile = open(const.PATH_SEND + filename + ".mp4", "r")
    os.fsync(videofile.fileno())
    videofile.close()

    textfile = open(const.PATH_SEND + filename + ".tx_","w")
    textfile.write(timenow)
    textfile.flush()
    os.fsync(textfile.fileno())
    textfile.close()
    os.rename(const.PATH_SEND + filename + ".tx_", const.PATH_SEND + filename + ".txt")
    
    time.sleep(1)

    
    #print("curl -i --connect-timeout 10 --max-time 15 -F id='" + str(const.getserial()) + 
    #            "' -F date='" + timenow + "' -F filename='" + filename + ".mp4" + 
    #            "' -F filedata=@" + filename + " " + const.URL_DATA + "")
    if (const.internet_on()):
        #GPIO.output(const.SEND, True)
        try:

            retry_send = subprocess.call("curl -i --connect-timeout 10 --max-time 15 -F id='" + str(const.getserial()) + 
                        "' -F date='" + timenow + 
                        # "' -F filename='" + filename + ".ts" +
                        "' -F filename='" + filename + ".mp4" +
                        "' " + const.URL_DATA + " > " + const.PATH_LOG + "/vr_curl.log", shell=True)
        except:
            print("curl1 error")
        
        #GPIO.output(const.SEND, False)
    print("Working process ended")

def gpio_callback(channel):
    '''
    Gpio callback function (compatible)
    Stop video and audio recording
    Spawn working process
    '''
    global lock
    if lock: return
    lock = 1
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    print(timenow)      
    print("Button triggered")
    # Save video to file
    # subprocess.call("touch " + const.PATH_PICAM + "hooks/start_record", shell=True)
    # time.sleep(10)
    # subprocess.call("touch " + const.PATH_PICAM + "hooks/stop_record", shell=True)
    #
    #stop raspivid
    os.kill(proc.pid, signal.SIGUSR1)
    #stop audio stream
    stream.stop_stream()
    time.sleep(2) # Wait raspivid
    Process(target=P0, args=()).start()	# Start the subprocess
    time.sleep(1) # Wait P0 to start
    print("Callback function ended")
    lock = 0

def audio_callback(in_data, frame_count, time_info, status):
    '''
    Audio callback function
    Append 441 audio frames to audio buffer dequeue
    '''
    audio_buffer.append(in_data)
    return (None, pyaudio.paContinue)

if __name__ == '__main__':
    try:
        '''
        Main thread
        '''
        sending = 0
        lock = 0
        GPIO_setup()

        audio_buffer = deque([], 1200)  # 1200*0.1s = 120s
        p = pyaudio.PyAudio()

        m = hashlib.md5() #md5 calculator

        stream = p.open(format=pyaudio.paInt16,
                        channels=2,
                        rate=44100,
                        input=True,
                        frames_per_buffer=44100 // 10,
                        stream_callback=audio_callback)

        timenow = time.strftime("%Y-%m-%d %H:%M:%S")
        print(timenow)

        #Start raspivid
        subprocess.call("killall raspivid", shell=True)
        cmd = "/usr/bin/raspivid -c -o /home/pi/out.h264 -s -t 60000 -b 1100000 -rot 180"
        # subprocess.call("killall picam", shell=True)
        # os.chdir(const.PATH_PICAM)
        # cmd = const.PATH_PICAM + "picam --alsadev hw:1,0 --rotation 180 -f 25 -g 50 --recordbuf 55"
        proc = subprocess.Popen(cmd.split(), shell=False)
        print("raspivid started")
        #start audio stream
        stream.start_stream()
        time.sleep(1)
        GPIO.output(const.READY, True)

        #Main loop
        while True:
            #check if video capture running
            if (proc.poll() <> None):
                #print("picam process not found. Restarting")
                print("raspivid process not found. Restarting")
                time.sleep(2)
                proc = subprocess.Popen(cmd.split(), shell=False)
                time.sleep(1)

            #if GPIO.event_detected(const.SWITCH):
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            if status == MIFAREReader.MI_OK:
                print("Card detected")
            (status,backData) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                if backData in const.RFC_CARDS:
                    GPIO.output(const.READY, False)
                    lock = 1
                    gpio_callback(1) #Actually we don't need separate callback function
                    GPIO.output(const.READY, True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Ctrl-C pressed")
        GPIO.output(const.READY, False)

    except Exception as e:
        print(e)

    finally:
        MIFAREReader.GPIO_CLEEN()
        GPIO.cleanup()
        stream.close()
        proc.terminate()
