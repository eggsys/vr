#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import os
import subprocess
import signal
import md5
from multiprocessing import Process

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
    return cpuserial

def P0():
    global sending

    print("Working process started")
    GPIO.output(SEND, True)
    sending += 1
    # check file creation
    if (not os.path.isfile("/home/pi/out.h264")):
        return
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    filename = md5.new(getserial() + str(int(time.mktime(time.strptime(timenow,"%Y-%m-%d %H:%M:%S"))))).hexdigest() + ".mp4"
    textfile = open("/home/pi/send/" + filename[0:32] + ".txt","w")
    subprocess.call("MP4Box -add /home/pi/out.h264 /home/pi/send/out.mp4", shell=True)
    os.rename("/home/pi/send/out.mp4", "/home/pi/send/" + filename)
    textfile.write(timenow)
    textfile.close
    print("curl -i -F id='" + str(getserial()) + 
                "' -F date='" + timenow + "' -F filename='" + filename + 
                "' -F filedata=@" + filename + " http://pm1.odwr.ru/sync")
    try:
        retry_send = subprocess.call("curl -i -F id='" + str(getserial()) + 
                    "' -F date='" + timenow + 
                    "' -F filename='" + filename +
                    "' http://pm1.odwr.ru/sync > /home/pi/curl.log", shell=True)
    except:
        print("curl1 error")
    retry_send = 1
    while retry_send:
        try:
            retry_send = subprocess.call("curl -i -F id='" + str(getserial()) + 
                        "' -F date='" + timenow + 
                        "' -F filename='" + filename +
                        "' -F filedata=@" + "/home/pi/send/" + filename + " http://pm1.odwr.ru/sync > /home/pi/curl.log", shell=True)
        except:
            print("curl2 error")
        time.sleep(1)
    os.remove("/home/pi/send/" + filename)
    os.remove("/home/pi/send/" + filename[0:32] + ".txt")
    sending -= 1
    if (sending <= 0):
        sending = 0
        GPIO.output(SEND, False)
    print("Working process ended")

def gpio_callback(channel):
    print("Button triggered")
    os.kill(proc.pid, signal.SIGUSR1)
    time.sleep(2) # Wait raspivid
    Process(target=P0, args=()).start()	# Start the subprocess
    time.sleep(1) # Wait P0 to start
    print("Callback function ended")

try:
    sending = 0
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    SWITCH = 21
    READY = 20
    SEND = 16
    GPIO.setup(SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(READY,GPIO.OUT)
    GPIO.setup(SEND,GPIO.OUT)
    GPIO.add_event_detect(SWITCH, GPIO.RISING, bouncetime = 80) 

    #Start raspivid
    subprocess.call("killall raspivid", shell=True)
    cmd = "/usr/bin/raspivid -c -o /home/pi/out.h264 -s -t 120000 -b 1100000 -rot 180"
    proc = subprocess.Popen(cmd.split(), shell=False)
    print("raspivid started")
    time.sleep(1)
    GPIO.output(READY, True)

    #Main loop
    while True:
        if (proc.poll() <> None):
            print("raspivid process not found. Restarting")
            time.sleep(2)
            proc = subprocess.Popen(cmd.split(), shell=False)
            time.sleep(1)
        if GPIO.event_detected(SWITCH):
            GPIO.output(READY, False)
            GPIO.remove_event_detect(SWITCH)
            gpio_callback(SWITCH)
            GPIO.add_event_detect(SWITCH, GPIO.RISING, bouncetime = 80)
            GPIO.output(READY, True)
        time.sleep(0.1)
    
except KeyboardInterrupt:
    print("Ctrl-C pressed")
    GPIO.output(READY, False)
    GPIO.cleanup()
    
finally: 
    proc.terminate()