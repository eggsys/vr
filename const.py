#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2

URL_DOMAIN  = "http://pm1.odwr.ru/"
#URL_DOMAIN  = "http://pm1.euct.ru/"
URL_DATA    = URL_DOMAIN + "sync"
URL_UPDATE  = URL_DOMAIN + "sync/update"
PATH_BASE   = "/home/pi/"
PATH_VR     = PATH_BASE + "vr/"
PATH_SEND   = PATH_BASE + "send/"
PATH_UPDATE = PATH_BASE + "update/"
#PATH_PICAM 	= PATH_BASE + "picam/"
PATH_BACKUP = PATH_BASE + "backup"
PATH_LOG    = PATH_BASE + "log/"
RFC_CARDS   = ([68,72,50,208,238],[215,30,104,133,36])

READY = 38
SEND = 36
    
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

def internet_on():
    try:
        response=urllib2.urlopen(URL_DOMAIN,timeout=3)
        return True
    except urllib2.URLError as err: pass
    return False
