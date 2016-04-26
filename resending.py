#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import os
import subprocess
import fnmatch

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

def list_files(path, ext):
    # returns a list of names (with extension, without full path) of all files 
    # in folder path
    files = []
    for name in os.listdir(path):
        if (os.path.isfile(os.path.join(path, name)) and fnmatch.fnmatch(name, ext)):
            files.append(name)
    return files 

try:
    filelist = list_files("/home/pi/send/","*.txt")
    for f in filelist:
        tf = open(os.path.join("/home/pi/send/", f),'r')
        fileinfo = tf.read()
        tf.close()
        filename = f[0:32] + ".mp4"
        # check file creation
        if (not os.path.isfile(os.path.join("/home/pi/send/", filename))):
            break
        print("curl -i -F id='" + str(getserial()) + 
                    "' -F date='" + fileinfo + "' -F filename='" + filename + 
                    "' -F filedata=@" + filename + " http://pm1.odwr.ru/sync")
        retry_send = 1
        while retry_send:
            try:
                retry_send = subprocess.call("curl -i -F id='" + str(getserial()) + 
                            "' -F date='" + fileinfo + 
                            "' -F filename='" + filename +
                            "' -F filedata=@" + "/home/pi/send/" + filename + " http://pm1.odwr.ru/sync > /home/pi/send/curl.log", shell=True)
            except:
                print("curl_resend error")
            time.sleep(1)
        os.remove(os.path.join("/home/pi/send/", filename))
        os.remove(os.path.join("/home/pi/send/", filename[0:32] + ".txt"))

except KeyboardInterrupt:
    print("Ctrl-C pressed")
