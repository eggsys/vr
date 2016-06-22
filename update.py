#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import os
import subprocess
import zipfile
import shutil
import time
import const
from shutil import copyfile

def GPIO_setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(const.READY,GPIO.OUT)
    GPIO.setup(const.SEND,GPIO.OUT)

try:
    time.sleep(10) #sleep 10 sec. for better usb modem init ...  but i think it doesn't help
    GPIO_setup()
    count = 20
    
    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    print(timenow)
    print("Finding internet... ")
    while not const.internet_on() and count > 0:
        GPIO.output(const.READY, True)
        time.sleep(1)
        GPIO.output(const.READY, False)
        time.sleep(5)
        count -=1
        print("No internet... retry "+str(count))
    
    if (const.internet_on()):
        
        #send logs to the server
        filename="log.zip"

        #copy umtskeeper.log
        if (os.path.isfile("/var/log/umtskeeper.log")):
            copyfile("/var/log/umtskeeper.log", const.PATH_LOG + "umtskeeper.log")
        #remove old zip
        if (os.path.isfile(const.PATH_BASE + "log.zip")):
            os.remove(const.PATH_BASE + "log.zip")
            
        cmd = ("zip -rq " + const.PATH_BASE + filename + " " + const.PATH_LOG + "*")
        print(cmd)
        
        try:
            update = subprocess.call(cmd, shell=True)
        except:
            print("Zip logs failed")
        
        GPIO.output(const.SEND, False)
        
        if (os.path.isfile(const.PATH_BASE + filename)):
            try:
                print("Upload logs")
                cmd = ("curl --connect-timeout 15 --max-time 300 --silent " + 
                                "-F id='" + str(const.getserial()) + "' " +
                                "-F filename='" + filename + "' " +
                                "-F filedata=@" + const.PATH_BASE + filename + " " + const.URL_UPDATE + "")
                print(cmd)
                update = subprocess.call(cmd, shell=True)
                
                #for file in os.listdir(const.PATH_LOG):
                #    os.remove(os.path.join(const.PATH_LOG,file))
                os.remove(const.PATH_BASE + "log.zip")
            except:    
                print("Upload logs error")
            
        #get update
        print("Try update...")
        cmd = ("curl -L --connect-timeout 15 --max-time 30 " + 
                      "-F id='" + str(const.getserial()) + "' " + 
                      const.URL_UPDATE + " > " + const.PATH_BASE + "update.zip")
        print(cmd)
        update = subprocess.call(cmd, shell=True)
        
        if (os.path.isfile(const.PATH_BASE + "update.zip")):
            try:
                with zipfile.ZipFile(const.PATH_BASE + "update.zip", "r") as myzip:
                    for f in myzip.namelist():
                         myzip.extract(f, path=const.PATH_UPDATE)
                    for name in os.listdir(const.PATH_UPDATE):
                        if (os.path.isfile(const.PATH_UPDATE+name)):
                            print("copyfile("+const.PATH_UPDATE+name+","+const.PATH_VR+name+")")
                            copyfile(const.PATH_UPDATE+name, const.PATH_VR+name)
            except:    
                print("Update failed")
            for file in os.listdir(const.PATH_UPDATE):
                os.remove(os.path.join(const.PATH_UPDATE,file))
            #os.remove(const.PATH_BASE + "update.zip")

    GPIO.cleanup() 
    cmd_resend  = "stdbuf -oL /usr/bin/python " + const.PATH_VR + "resending.py" + " >> " + const.PATH_LOG + "resending.log"
    cmd_vr      = "stdbuf -oL /usr/bin/python " + const.PATH_VR + "vr.py"        + " >> " + const.PATH_LOG + "vr.log"
    
    print("Run resend: "+cmd_resend)
    #proc_resend = subprocess.Popen(cmd_resend.split(), shell=False)
    proc_resend = subprocess.Popen(cmd_resend, shell=True)
    time.sleep(3)
    
    print("Run vr: "+cmd_vr)
    #proc_vr = subprocess.Popen(cmd_vr.split(), shell=False)
    proc_vr = subprocess.Popen(cmd_vr, shell=True)
    
except KeyboardInterrupt:
    print("Ctrl-C pressed")
    GPIO.cleanup()          
#except Exception, e:
#    print("Exception: "+ str(e))
#    GPIO.cleanup()
#finally:
#    GPIO.cleanup()
