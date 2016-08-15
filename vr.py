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
import md5
from multiprocessing import Process
import const

def GPIO_setup():
    global MIFAREReader
    MIFAREReader = MFRC522.MFRC522()
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(const.SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(const.READY,GPIO.OUT)
    #GPIO.setup(const.SEND,GPIO.OUT)
    #GPIO.add_event_detect(const.SWITCH, GPIO.RISING, bouncetime = 250) 

def P0():
    global sending

    print("Working process started")
    
    sending += 1
    # check file creation
    #if (not os.path.isfile(const.PATH_PICAM + "rec/*.ts")):
    #    print('no file')
    #    return
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    filename = md5.new(const.getserial() + str(int(time.mktime(time.strptime(timenow,"%Y-%m-%d %H:%M:%S"))))).hexdigest()
    newest = max(glob.iglob(const.PATH_PICAM + 'rec/*.[Tt][Ss]'), key=os.path.getctime)
    #subprocess.call("MP4Box -add " + const.PATH_BASE + "out.h264 " + const.PATH_SEND + "out.mp4", shell=True)
    #os.rename(newest, const.PATH_SEND + filename + ".ts")
    shutil.copyfile(newest, const.PATH_SEND + filename + ".ts",follow_symlinks=True)
    videofile = open(const.PATH_SEND + filename + ".ts","r")
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
    if (0):#(const.internet_on()):
        #GPIO.output(const.SEND, True)
        try:
            retry_send = subprocess.call("curl -i --connect-timeout 10 --max-time 15 -F id='" + str(const.getserial()) + 
                        "' -F date='" + timenow + 
                        "' -F filename='" + filename + ".ts" +
                        "' " + const.URL_DATA + " > " + const.PATH_LOG + "/vr_curl.log", shell=True)
        except:
            print("curl1 error")
        
        #GPIO.output(const.SEND, False)
    print("Working process ended")

def gpio_callback(channel):
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    print(timenow)      
    print("Button triggered")
    # Save video to file
    subprocess.call("touch " + const.PATH_PICAM + "hooks/start_record", shell=True)
    time.sleep(10)
    subprocess.call("touch " + const.PATH_PICAM + "hooks/stop_record", shell=True)
    #
    #time.sleep(2) # Wait raspivid
    Process(target=P0, args=()).start()	# Start the subprocess
    time.sleep(1) # Wait P0 to start
    print("Callback function ended")

try:
    sending = 0
    GPIO_setup()

    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    print(timenow)

    #Start raspivid
    subprocess.call("killall picam", shell=True)
    os.chdir(const.PATH_PICAM)
    cmd = const.PATH_PICAM + "picam --alsadev hw:1,0 --rotation 180 -f 25 -g 50 --recordbuf 55"
    proc = subprocess.Popen(cmd.split(), shell=False)
    print("picam started")
    time.sleep(1)
    GPIO.output(const.READY, True)

    #Main loop
    while True:
        if (proc.poll() != None):
            print("picam process not found. Restarting")
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
                #GPIO.remove_event_detect(const.SWITCH)
                #gpio_callback(const.SWITCH)
                gpio_callback(1)
                #GPIO.add_event_detect(const.SWITCH, GPIO.RISING, bouncetime = 80)
                GPIO.output(const.READY, True)
        time.sleep(0.1)
    
except KeyboardInterrupt:
    print("Ctrl-C pressed")
    GPIO.output(const.READY, False)
    MIFAREReader.GPIO_CLEEN()
    #GPIO.cleanup()

except Exception as e: print(e)
    
finally:
    MIFAREReader.GPIO_CLEEN()    
    #GPIO.cleanup()
    proc.terminate()
