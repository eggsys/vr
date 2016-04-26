#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import zipfile
import subprocess
import shutil
import time

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

try:
    print("curl -F id='" + str(getserial()) + "' http://pm1.odwr.ru/sync/update > /home/pi/update.zip")
    count = 100
    while count > 0:
        if (not subprocess.call("curl -F id='" + str(getserial()) + "' http://pm1.odwr.ru/sync/update > /home/pi/update.zip", shell=True)):
             count = 1
        count -= 1
        time.sleep(1)
    if (not os.path.isfile("/home/pi/update.zip")):
        quit()
    try:
        with zipfile.ZipFile("/home/pi/update.zip", "r") as myzip:
            for f in myzip.namelist():
                 myzip.extract(f, path="/home/pi/update")
        if (os.path.isfile("/home/pi/update/vr.py")):
            if (os.path.isfile("/home/pi/backup/vr.py")):
                os.remove("/home/pi/backup/vr.py")
            os.rename("/home/pi/vr/vr.py","/home/pi/backup/vr.py")
            os.rename("/home/pi/update/vr.py","/home/pi/vr/vr.py")
        if (os.path.isfile("/home/pi/update/resending.py")):
            if (os.path.isfile("/home/pi/backup/resending.py")):
                os.remove("/home/pi/backup/resending.py")
            os.rename("/home/pi/vr/resending.py","/home/pi/backup/resending.py")
            os.rename("/home/pi/update/resending.py","/home/pi/vr/resending.py")
        if (os.path.isfile("/home/pi/update/update.py")):
            if (os.path.isfile("/home/pi/backup/update.py")):
                os.remove("/home/pi/backup/update.py")
            os.rename("/home/pi/vr/update.py","/home/pi/backup/update.py")
            os.rename("/home/pi/update/update.py","/home/pi/vr/update.py")
    except:
        if (os.path.isfile("/home/pi/backup/vr.py")):
            if (os.path.isfile("/home/pi/vr/vr.py")):
                os.remove("/home/pi/vr/vr.py")
            shutil.copy("/home/pi/backup/vr.py","/home/pi/vr/vr.py")
        if (os.path.isfile("/home/pi/backup/resending.py")):
            if (os.path.isfile("/home/pi/vr/resending.py")):
                os.remove("/home/pi/vr/resending.py")
            shutil.copy("/home/pi/backup/resending.py","/home/pi/vr/resending.py")        
        if (os.path.isfile("/home/pi/backup/update.py")):
            if (os.path.isfile("/home/pi/vr/update.py")):
                os.remove("/home/pi/vr/update.py")
            shutil.copy("/home/pi/backup/update.py","/home/pi/vr/update.py")        
        print("Update failed")
    for file in os.listdir("/home/pi/update"):
        os.remove(os.path.join("/home/pi/update",file))
    os.remove("/home/pi/update.zip")

    cmd_resend = "/usr/bin/python /home/pi/vr/resending.py"
    cmd_vr = "/usr/bin/python /home/pi/vr/vr.py"
    proc_resend = subprocess.Popen(cmd_resend.split(), shell=False)
    proc_vr = subprocess.Popen(cmd_vr.split(), shell=False)

except KeyboardInterrupt:
    print("Ctrl-C pressed")
