#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import os
from subprocess import Popen, PIPE, STDOUT
import signal
import fnmatch
import const

def GPIO_setup():
    GPIO.setmode(GPIO.BOARD)
    SEND = 16
    GPIO.setup(const.SEND,GPIO.OUT)
    #GPIO.cleanup()
    
def list_files(path, ext):
    # returns a list of names (with extension, without full path) of all files 
    # in folder path
    files = []
    for name in os.listdir(path):
        if (os.path.isfile(os.path.join(path, name)) and fnmatch.fnmatch(name, ext)):
            files.append(name)
    return files 

try:
    GPIO_setup()

    timenow = time.strftime("%Y-%m-%d %H:%M:%S")
    print(timenow)

    print("Resending started")
    #rename .tx_ files to .txt (if found)
    try:
        filelist = list_files(const.PATH_SEND,"*.tx_")
        for f in filelist:
            print("os.rename("+const.PATH_SEND + f+", "+const.PATH_SEND + f[0:32] + ".txt"+")")
            os.rename(const.PATH_SEND + f, const.PATH_SEND + f[0:32] + ".txt")
    except:
        print("Rename error")
    #main loop
    while True:
        if (const.internet_on()):
            try:
                filelist = list_files(const.PATH_SEND,"*.txt")
                for f in filelist:
                    tf = open(os.path.join(const.PATH_SEND, f),'r')
                    fileinfo = tf.read()
                    tf.close()
                    
                    filename = f[0:32] + ".ts"
                    # check file creation
                    if (not os.path.isfile(os.path.join(const.PATH_SEND, filename))):
                        break
                    GPIO.output(const.SEND, True)
                    cmd = ("curl --connect-timeout 15 --max-time 300 --silent " + 
                                "-F id='" + str(const.getserial()) + "' " +
                                "-F date='" + fileinfo + "' " +
                                "-F filename='" + filename + "' " +
                                "-F filedata=@" + const.PATH_SEND + filename + " " + const.URL_DATA + "")
                    print(cmd)
                    try:
                        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,stderr=STDOUT, close_fds=True)
                        result = p.stdout.read()
                        print("Result: " + result)
                        if result == "Success":
                            print("Remove "+filename)
                            os.remove(os.path.join(const.PATH_SEND, filename))
                            os.remove(os.path.join(const.PATH_SEND, filename[0:32] + ".txt"))
                    #except:
                    #    print("Curl error")
                    except Exception, e:
                        print("Curl error: "+ str(e))
                    GPIO.output(const.SEND, False)
            except KeyboardInterrupt:
                print("Ctrl-C pressed")
        else:
            print("No internet")
        #print("Sleep 5 seconds...")
        time.sleep(5)
except KeyboardInterrupt:
    print("Ctrl-C pressed")
    GPIO.cleanup()
except Exception, e:
    print("Eerror:"+ str(e))
    #GPIO.cleanup()
finally:
    GPIO.cleanup()
