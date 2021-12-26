import os
import requests
import json
import serial.tools.list_ports
import paho.mqtt.client as mqttclient
import time
import  sys
feeds = ['linhla/feeds/error_control','linhla/feeds/HCM_Temp','linhla/feeds/LED','linhla/feeds/MICROBIT_TEMP','linhla/feeds/microbit-humid']
#     feeds subscription

#     utilities function
def connected(client, userdata, flags, rc):
    if rc==0:
        for f in feeds:
            print("subscibing to " + f)
            client.subscribe(f)
        print("connected")
    else:
        print('Failed to connect')
    loop_flag = 0
def subscribed(client , userdata , mid , granted_qos):
    print ("successfully subscribed!")

def msg(client, userdata, message):
    print("Received "+ message.payload.decode('UTF-8') + " from " + str(message.topic))
    if str(message.topic) == "linhla/feeds/LED":
        client.publish("linhla/feeds/error_control", "{ACK-LED:" + str(message.payload.decode('UTF-8')) + "}")
        ser.write(message.payload)

def disconnected(client):
    print("Disconnected..")
    sys.exit(1)


def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        if "com0com" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    print(commPort)
    return commPort


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    if splitData[0] == "TEMP":
        client.publish("linhla/feeds/MICROBIT_TEMP", splitData[1])
    if splitData[0] == "HUMI":
        client.publish("linhla/feeds/microbit-humid", splitData[1])
mess = ""
def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + str(ser.read(bytesToRead).decode("UTF-8"))
        print(mess)
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]
#     open_weather_map
weather_key = os.environ.get('weather_map_key')
HCM_ID = 1566083
def kToc(kelvin):
    return kelvin - 273

def getHCMtemp():
    url = f"https://api.openweathermap.org/data/2.5/weather?id={HCM_ID}&appid={weather_key}"
    re = requests.get(url)
    data = re.json()
    currTemp = data['main']['temp']
    formattedTemp = '{:.2f}'.format(kToc(currTemp))
    return formattedTemp
def getHCMhumid():
    url = f"https://api.openweathermap.org/data/2.5/weather?id={HCM_ID}&appid={weather_key}"
    re = requests.get(url)
    data = re.json()
    currHumid = data['main']['humidity']
    return currHumid
#     broker_address : adafruit IPv4 address

broker_address = "52.54.163.195"

#     connection set up
client = mqttclient.Client()
client.username_pw_set("linhla", os.environ.get("AIO_KEY"))
client.on_connect = connected
client.on_subscribe =subscribed
client.on_message = msg


print("connecting to broker")
client.connect(broker_address)
client.loop_start()
#     error control
waiting_counter = 0
sending_mess_again = False
#     microbit stuff
isMicrobitConnected = False
if getPort() != "None":
     isMicrobitConnected = True
ser = serial.Serial(port=getPort(), baudrate=115200)
#     loop
loop_flag = 1
while loop_flag == 1:

    if isMicrobitConnected:
        readSerial()
    if waiting_counter > 0:
        waiting_counter -= 1;
        if waiting_counter == 0:
            sending_mess_again = True
    if sending_mess_again:
        client.publish("linhla/feeds/MICROBIT_TEMP","123")
    time.sleep(3)
client.disconnect()
client.loop_stop()