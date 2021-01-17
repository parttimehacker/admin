#!/usr/bin/python3
""" DIYHA admin
    Send web server information from MQTT broker
"""

# The MIT License (MIT)
#
# Copyright (c) 2019 parttimehacker@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging.config
import time
import paho.mqtt.client as mqtt
import requests

from pkg_classes.configmodel import ConfigModel
from pkg_classes.statusmodel import StatusModel

# Start logging and enable imported classes to log appropriately.

LOGGING_FILE = '/usr/local/admin/logging.ini'
logging.config.fileConfig( fname=LOGGING_FILE, disable_existing_loggers=False )
LOGGER = logging.getLogger(__name__)
LOGGER.info('Application started')

# get the command line arguements

CONFIG = ConfigModel(LOGGING_FILE)


# send email on critical events

def send_alert_email(title, message):
    """ send email to Dave and Joann """
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("parttimehacker@gmail.com", "qcbgbnhaybzcehpu")
        mailtext = "Subject: "+title+"\n"+message
        server.sendmail(
            "parttimehacker@gmail.com",
            "parttimemaker@gmail.com",
            mailtext)
        server.sendmail(
            "parttimehacker@gmail.com",
            "jgperrett@cywren.com",
            mailtext)
    except smtplib.SMTPException as exception:
        LOGGER.info('send_alert_mail exception: ' +str(exception))
    server.quit()


def post_server_status(msg):
    """ send server status to diyha webserver API path
    """
    url = CONFIG.get_webserver_api_url()
    payload = str( msg.payload, 'utf-8' )
    fields = msg.topic.split('/')
    api_key = fields[2]
    hostname = fields[1]
    api_url = url + "?server=" + hostname + "&" + api_key + "=" + payload
    response = requests.get(api_url)
    
    
# post API message on diyha system status

def post_system_status(msg):
    """ send status to diyha web server at api/ path
    """
    url = CONFIG.get_webserver_api_url()
    payload = str( msg.payload, 'utf-8' )
    fields = msg.topic.split('diy/system/')
    status = fields[1]
    api_url = url + "?status=" + status + "&state=" + payload
    response = requests.get(api_url)
    

def email_critical_system_status(msg): 
    """ process alert and fire system messages
    """
    #pylint: disable=unused-argument
        
    payload =  str( msg.payload, 'utf-8' )
    LOGGER.info(msg.topic, payload)
    
    # only process two critical messages - ignoring the rest
    
    if msg.topic == 'diy/system/fire':
        subject = "FIRE ALERT DOWNGRADE"
        message = "DIYHAS: Fire alert terminated by Alexa or the console."
        if msg.payload == b'ON':
            subject = "FIRE ALERT"
            message = "DIYHAS: Fire alert initiated by Alexa or the console."
        send_alert_email(title,message)
        
    elif msg.topic == 'diy/system/panic':
        subject = "PANIC ALERT DOWNGRADE"
        message = "DIYHAS: Panic alert terminated by Alexa or the console."
        if msg.payload == b'ON':
            subject = "PANIC ALERT"
            message = "DIYHAS: Panic alert initiated by Alexa or the console."
        send_alert_email(title,message)
        

# The callback for when a PUBLISH message is received from the server
def on_message(client, user_data, msg):
    """ dispatch to the appropriate MQTT topic handler 
    """
    #pylint: disable=unused-argument
    if msg.topic == 'diy/system/who':
        WHO.message(msg)
    elif 'system' in msg.topic:
        post_system_status(msg)
        email_critical_system_status(msg)
    else:
        post_server_status(msg)


def on_connect(client, userdata, flags, rc_msg):
    """ Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
    """
    # pylint: disable=unused-argument
    client.subscribe("diy/system/calibrate", 1)
    client.subscribe("diy/system/demo", 1)
    client.subscribe("diy/system/fire", 1)
    client.subscribe("diy/system/panic", 1)
    client.subscribe("diy/system/security", 1)
    client.subscribe("diy/system/silent", 1)
    client.subscribe("diy/system/who", 1)
    client.subscribe("diy/+/os", 1)
    client.subscribe("diy/+/pi", 1)
    client.subscribe("diy/+/ip", 1)
    client.subscribe("diy/+/cpu", 1)
    client.subscribe("diy/+/cpucelsius", 1)


def on_disconnect(client, userdata, rc_msg):
    """ Subscribing on_disconnect() tilt """
    # pylint: disable=unused-argument
    client.connected_flag = False
    client.disconnect_flag = True
    
    
def initialize_system_topics(client,):
    """ dispatch system messages to subscribers """
    client.publish("diy/system/calibrate", "OFF", 0, True)
    client.publish("diy/system/demo", "ON", 0, True)
    client.publish("diy/system/fire", "OFF", 0, True)
    client.publish("diy/system/panic", "OFF", 0, True)
    client.publish("diy/system/security", "OFF", 0, True)
    client.publish("diy/system/silent", "OFF", 0, True)
    client.publish("diy/system/who", "OFF", 0, True)
    client.publish("diy/system/test", "OFF", 0, True)
    LOGGER.info("Publish / initalize eight (8) system topics")
    
def initialize_sensor_topics(client,):
    """ dispatch locations to sensor servers """
    client.publish("diy/choke/setup", "diy/main/living", 0, True)
    client.publish("diy/cloud/setup", "diy/main/garage", 0, True)
    client.publish("diy/cran/setup", "diy/upper/study", 0, True)
    LOGGER.info("Publish locations to three (3) sensor servers")

def initialize_clock_topics(client,):
    """ dispatch locations to clock servers """
    client.publish("diy/tay/setup", "diy/main/living", 0, True)
    client.publish("diy/bar/setup", "diy/upper/study", 0, True)
    client.publish("diy/bil/setup", "diy/upper/guest", 0, True)
    LOGGER.info("Publish locations to three (3) clock servers")

def initialize_light_topics(client,):
    """ dispatch locations to light servers """
    client.publish("diy/bear/setup", "diy/main/garage", 0, True)
    client.publish("diy/esp_0d9c84", "diy/main/kitchen", 0, True)
    LOGGER.info("Publish locations to one (1) light servers")

def initialize_alarm_topics(client,):
    """ dispatch locations to alarm servers """
    client.publish("diy/mul/setup", "diy/upper/guest", 0, True)
    client.publish("diy/esp_47aa10", "diy/upper/study", 0, True)
    client.publish("diy/esp_8fda09", "diy/upper/guest", 0, True)
    client.publish("diy/esp_47104c", "diy/main/garage", 0, True)
    LOGGER.info("Publish locations to three (3) alarm servers")


if __name__ == '__main__':

    # Setup MQTT handlers then wait for timed events or messages

    CLIENT = mqtt.Client()
    CLIENT.on_connect = on_connect
    CLIENT.on_disconnect = on_disconnect
    CLIENT.on_message = on_message
    
    # initialize status monitoring

    STATUS = StatusModel(CLIENT)
    STATUS.start()

    # command line argument for the switch mode - motion activated is the default

    CLIENT.connect(CONFIG.get_broker(), 1883, 60)
    CLIENT.loop_start()

    time.sleep(2) # let MQTT stuff initialize
    
    # set the state of overall system at all diyha devices
    
    initialize_system_topics(CLIENT)
    initialize_clock_topics(CLIENT)
    initialize_sensor_topics(CLIENT)
    initialize_clock_topics(CLIENT)
    initialize_alarm_topics(CLIENT)

    # Loop forever waiting for motion

    while True:
        time.sleep(2.0)

