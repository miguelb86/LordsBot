#!/usr/bin/env python3

from ppadb.client import Client
from PIL import Image
import numpy as np
import time
import pytesseract
import subprocess
import os
import mysql.connector
import datetime
import threading
import cv2
import traceback
import sys
import mss

from matplotlib import pyplot as plt
xoffset = 180
yoffset = 320
emulatorname = "emulator-5554"

def initmysql():
    cnx = mysql.connector.connect(user='root', password="lords", database='lords')
    cnx.autocommit=True
    return cnx

def mysqlCursor(cnx):
    return cnx.cursor()

def execQuery(cursor, query):
    query = (query)
    cursor.execute(query)
    return cursor

def closeconnections(cnx,cursor):
    cnx.close()
    cursor.close()

#nRZv+oQiUrrdjeWP
def connect(deviceid):
    try:
        cnx = initmysql()
        cursor = mysqlCursor(cnx)
        query = execQuery(cursor,  "SELECT port,name FROM lords.devices where id=" + str(deviceid))
        field_name = [field[0] for field in query.description]
        result_set = query.fetchone()
        if result_set!=None :
            row = dict(zip(field_name, result_set))
            portNo=int(row['port'])
            emulatorname=row['name']
        else :
            portNo=5037
        print("name ",emulatorname)
        adb = Client(host='127.0.0.1', port=portNo)
        devices = adb.devices()
        if len(devices) == 0:
            print('no device attached')
            quit()
        device = adb.device(emulatorname)
        return device
    except():
        quit()

def getTesseract(file) :
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    #result =pytesseract.image_to_string(Image.open(file), config='--psm 7').strip()
    image = cv2.imread(file) 
    cv2.dilate(image, (5, 5), image)
    result=pytesseract.image_to_string(image, config='--psm 7').strip()
    return result

def cropImageandProcess(file,x1,y1,x2,y2):
    image = Image.open(file+'.png')#.convert('L')
    left = x1
    top = y1
    right = x2
    bottom = y2
    cropped=image.crop((left, top, right, bottom))
    cropped.save(file+'.png', 'PNG')
    return getTesseract(file+'.png')
    

def checkShield(device, fails,emulatorid):
    try:
        cnx = initmysql()
        cursor = mysqlCursor(cnx)
        query = execQuery(cursor, "select addtime(datetime,addtime(time,-500))<now() shieldflag from shield where device = " + emulatorid + " order by id desc limit 1")
        field_name = [field[0] for field in query.description]
        result_set = query.fetchone()
        if result_set!=None :
            row = dict(zip(field_name, result_set))
            shieldflag=int(row['shieldflag'])
        else :
            shieldflag=1
        if (shieldflag!=0) :
            timeToShield(device,0,0,0)
            device.shell('input touchscreen tap 1850 350')
            time.sleep(1)
            image = device.screencap()
            with open('shield.png', 'wb') as f:
                f.write(image)
            with open('shieldnc.png', 'wb') as f:
                f.write(image)
            text = cropImageandProcess("shield",1150,550,1300,625).strip()
            device.shell('input touchscreen tap 1850 60')
            now = datetime.datetime.now()
            now = now.strftime('%Y-%m-%d %H:%M:%S')
            query = execQuery(cursor,"insert into shield (time,datetime,device) values ('" + text +"','" + now + "'," + emulatorid + ")")
        closeconnections(cnx,cursor)
    except:
        timeToShield(device,0,2,0)
        return 1

def timeToShield(device,hours,minutes,seconds):
        if(hours<1) :
            if(minutes<5) :
                shield(device)

def shield(device) :
    #print("Shielding")
    device.shell('input touchscreen tap 1850 350')
    device.shell('input touchscreen tap 850 550')
    device.shell('input touchscreen tap 1500 300')
    device.shell('input touchscreen tap 1150 500')
    device.shell('input touchscreen tap 1850 60')

def startLords(device) :
    pid=device.shell("pidof com.igg.android.lordsmobile")
    print("pid",pid)
    device.shell('monkey -p com.igg.android.lordsmobile -c android.intent.category.LAUNCHER 1')
    if (pid=="") :
        print("Starting Lords")
        time.sleep(25)
        #print("review squad",time.ctime())
        reviewSquad(device)
        device.shell('input touchscreen tap 1850 60')


def checkLogged(device) :
    image = device.screencap()
    with open('disconnected.png', 'wb') as f:
        f.write(image)
    text = cropImageandProcess("disconnected",900,450,1100,550).strip()
    print("revisando logged", text)
    if ( text == "Close") :
        device.shell('input touchscreen tap 900 520')
        time.sleep(2)
        startLords(device)
    elif (text == "Retry") :
        device.shell('input touchscreen tap 900 520')

def process_exists(process_name):
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    output = subprocess.check_output(call).decode()
    last_line = output.strip().split('\r\n')[-1]
    return last_line.lower().startswith(process_name.lower())

def checkEmulatorStatus(emulatorid) :
    device = connect(emulatorid)
    startLords(device)
    checkLogged(device)
    return device

def reviewSquad(device) :
    image = device.screencap()
    with open('squad.png', 'wb') as f:
        f.write(image)
    text = cropImageandProcess("squad",650,70,900,130).strip()
    if ( text[0:5] == "Squad") :
        device.shell('input touchscreen tap 1332 130')
        device.shell('input touchscreen tap 1550 60')

def collectBox(device,emulatorid) :
    try:
        cnx = initmysql()
        cursor = mysqlCursor(cnx)
            
        query = execQuery(cursor, "select addtime(datetime,duration)<now() misteryflag from lords.mistery where device = " + str(emulatorid) + " order by id desc limit 1")
        field_name = [field[0] for field in query.description]
        result_set = query.fetchone()
        if result_set!=None :
            row = dict(zip(field_name, result_set))
            misteryflag=int(row['misteryflag'])
        else :
            misteryflag=1
        if(misteryflag==1):
            device.shell('input touchscreen tap 1720 810')
            device.shell('input touchscreen tap 1100 750')
            time.sleep(2)
            image = device.screencap()
            with open('mistery'+emulatorid + '.png', 'wb') as f:
                f.write(image)
            text = cropImageandProcess("mistery"+emulatorid,1675,865,1750,900).replace(':', '').replace('(', '').replace(')', '').replace('}', '').replace('{', '')
            if (len(text)==0 or len(text)>4):
                    text="100"
            now = datetime.datetime.now()
            now = now.strftime('%Y-%m-%d %H:%M:%S')
            query = execQuery(cursor,"insert into mistery (duration,datetime, device) values ('" + text +"','" + now + "'," + emulatorid + ")")
            print("query insert into mistery (duration,datetime, device) values ('" + text +"','" + now + "'," + emulatorid + ")")
            print("not fail emulatorid",emulatorid)
            closeconnections(cnx,cursor)
    except Exception:
            now = datetime.datetime.now()
            now = now.strftime('%Y-%m-%d %H:%M:%S')
            print("fail emulatorid",emulatorid)
            query = execQuery(cursor,"insert into mistery (duration,datetime, device) values ('100','" + now + "'," + emulatorid + ")")
def reviewHelps(device,emulatorid) :
    image = device.screencap()
    with open('helps1'+emulatorid + '.png', 'wb') as f:
        f.write(image)
    with open('helps2'+emulatorid + '.png', 'wb') as f:
        f.write(image)
    text = cropImageandProcess("helps1"+emulatorid,1400,224,1520,260).strip().replace('/','').replace(':', '').replace('(', '').replace(')', '').replace('}', '').replace('{', '').replace(',', '')
    text2 = cropImageandProcess("helps2"+emulatorid,1520,224,1650,260).strip().replace('/','').replace(':', '').replace('(', '').replace(')', '').replace('}', '').replace('{', '').replace(',', '')
    return (not text=="" and text==text2)
    
def sendHelps(device,emulatorid) :
    cnx = initmysql()
    cursor = mysqlCursor(cnx)

    query = execQuery(cursor,"select count(*) total from lords.helps where 1=1 and date = date(now()) and device = " + emulatorid)
    field_name = [field[0] for field in query.description]
    result_set = query.fetchone()
    row = dict(zip(field_name, result_set))
    total=int(row['total'])
    print("Total ", total)
    if(total==0):
        print("insert into lords.helps (date,complete,cutout,device) values (date(now()),0,19,"+emulatorid +")")
        query = execQuery(cursor,"insert into lords.helps (date,complete,cutout,device) values (date(now()),0,19,"+emulatorid +")")
        print("insert helps")
    query = execQuery(cursor,"select count(*) total from lords.helps where 1=1 and complete = 1 and date = date(now()) and device = " + emulatorid)
    field_name = [field[0] for field in query.description]
    result_set = query.fetchone()
    row = dict(zip(field_name, result_set))
    total=int(row['total'])
    if(total==0) :
        device.shell('input touchscreen tap 890 1020')
        device.shell('input touchscreen tap 1780 720')
        device.shell('input touchscreen tap 360 620')
        device.shell('input touchscreen tap 1000 1000')
        sendhelpsflag=reviewHelps(device,emulatorid)
        if(sendhelpsflag==True):
            query = execQuery(cursor,"update lords.helps set complete =1 where 1=1 and complete = 0 and date = date(now()) and device = " + emulatorid)
        device.shell('input touchscreen tap 1900 60')
        device.shell('input touchscreen tap 1900 60')
        closeconnections(cnx,cursor)
def VIP(device) :
    cnx = initmysql()
    cursor = mysqlCursor(cnx) 
    query = execQuery(cursor, "select total,addtime(datetime,10000)<now() vipflag from lords.vip order by id desc limit 1")
    field_name = [field[0] for field in query.description]
    result_set = query.fetchone()
    row = dict(zip(field_name, result_set))
    closeconnections(cnx,cursor)
    vip=int(row['vipflag'])
    total=int(row['total'])
    #print("vip flag ", vip)
    if(vip==1 and total<=6) :
        total=total+1
        device.shell('input touchscreen tap 1000 850')
        device.shell('input touchscreen tap 1400 200')
        device.shell('input touchscreen tap 1150 600')
        device.shell('input touchscreen tap 800 600')
        device.shell('input touchscreen tap 450 600')
        device.shell('input touchscreen tap 1150 450')
        device.shell('input touchscreen tap 800 450')
        device.shell('input touchscreen tap 450 450')
        device.shell('input touchscreen tap 1550 60')
        now = datetime.datetime.now()
        now = now.strftime('%Y-%m-%d %H:%M:%S')
        query = execQuery(cursor,"insert into VIP (datetime,total) values ('" + now + "','" + str(total) + "')")

def readNotifications(device) :
    device=""

def main():
    m=0
    emulatorid = sys.argv[1]
    device = checkEmulatorStatus(emulatorid)
    fails = 0
    #drawRect(device)
    while True :
        if(m>60) :
            device = checkEmulatorStatus(emulatorid)
            checkLogged(device)
            
            m=0
        else :
            m=m+1
        #print("checking shield")
        #VIP(device)
        #readNotifications(device)

        #ya quedó reconfigurado
        fails=checkShield(device, fails,emulatorid)
        collectBox(device,emulatorid)
        sendHelps(device,emulatorid)
        
sct = mss.mss()

def drawRect(device):
    device.shell('screencap -p')
    
if __name__ == "__main__":
    main()