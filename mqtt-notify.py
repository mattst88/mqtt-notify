#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

# Relevant API docs:
#   https://pypi.org/project/paho-mqtt/
#   https://lazka.github.io/pgi-docs/#Notify-0.7
#   https://lazka.github.io/pgi-docs/#Secret-1
#   https://lazka.github.io/pgi-docs/#GLib-2.0
#   https://dbus.freedesktop.org/doc/dbus-python/dbus.mainloop.html

import argparse
import configparser
import re
import signal
import sys
import time
import paho.mqtt.client as mqtt
import gi
gi.require_version('Notify', '0.7')
gi.require_version('Secret', '1')
from gi.repository import GLib, Notify, Secret

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

chan_msg = re.compile(r'\[(?P<channel>#.*?)\]\n<\s*(?P<nick>.*?)> \| (?P<msg>.*)')
priv_msg = re.compile(r'\(PM: (?P<nick>.*?)\)\n(?P<msg>.*)')
subj_fmt = re.compile(r'IRC message (on|from) (?P<key>.*)')

notification_map = {}

class Signaler:
    def __init__(self, loop):
        self.loop = loop

    def handler(self, *_):
        self.loop.quit()

def on_connect(client, userdata, flags, rc):
    print("Connected")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(userdata)

def on_close(notification):
    key = ''
    if (m := subj_fmt.match(notification.props.summary)) is not None:
        key = m.group('key')

    if key in notification_map:
        for i in notification_map[key]:
            if i is not notification:
                i.close()
        del notification_map[key]

def on_message(client, userdata, msg):
    icon = '/usr/share/icons/HighContrast/scalable/apps-extra/internet-group-chat.svg'
    message = msg.payload.decode('utf-8')

    if (m := re.match(chan_msg, message)) is not None:
        subject = 'IRC message on {}'.format(m.group('channel'))
        body = '<{}> {}'.format(m.group('nick'), m.group('msg'))
        key = m.group('channel')
    if (m := re.match(priv_msg, message)) is not None:
        subject = 'IRC message from {}'.format(m.group('nick'))
        body = '<{}> {}'.format(m.group('nick'), m.group('msg'))
        key = m.group('nick')
    else:
        subject = 'IRC'
        body = message
        key = ''

    if key not in notification_map or len(notification_map[key]) == 1:
        n = Notify.Notification.new(subject, body, icon)
        n.set_category('im.received')
        n.connect('closed', on_close)

        if key not in notification_map:
            notification_map[key] = [n]
        else:
            notification_map[key].append(n)
    else:
        n = notification_map[key][1]
        n.update(subject, body, icon)

    n.show()

def on_disconnect(client, userdata, rc):
    print("Disconnected")

def password(user, host):
    # Insert password with secret-tool(1). E.g.,
    #   secret-tool store --label="mqtts://example.com" user myuser service mqtt host example.com

    schema = Secret.Schema.new("org.freedesktop.Secret.Generic",
        Secret.SchemaFlags.NONE,
        {
            "user": Secret.SchemaAttributeType.STRING,
            "service": Secret.SchemaAttributeType.STRING,
            "host": Secret.SchemaAttributeType.STRING,
        }
    )
    attributes = {
        "user": user,
        "service": "mqtt",
        "host": host,
    }

    while (pw := Secret.password_lookup_sync(schema, attributes, None)) is None:
        time.sleep(5)
    return pw

def config(filename):
    try:
        with open(filename) as file:
            config = configparser.ConfigParser()
            config.read_file(file)

            cfg = config[configparser.DEFAULTSECT]
            broker = cfg['broker']
            topic = cfg['topic']
            port = int(cfg['port'])
            user = cfg['user']

            return user, broker, port, topic
    except:
        print("Failed to parse {}".format(filename), file=sys.stderr)
        sys.exit(-1)

def main(argv):
    loop = GLib.MainLoop()

    do = Signaler(loop)
    signal.signal(signal.SIGINT,  do.handler)
    signal.signal(signal.SIGTERM, do.handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='configuration file',
        type=argparse.FileType('r'), required=True)
    args = parser.parse_args()

    user, broker, port, topic = config(args.config.name)

    Notify.init('MQTT to Notify bridge')
    client = mqtt.Client(userdata=topic)

    client.tls_set()
    client.username_pw_set(user, password(user, broker))
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.connect_async(broker, port, 60)

    client.loop_start()

    loop.run()

    client.loop_stop()
    client.disconnect()
    Notify.uninit()

if __name__ == '__main__':
    main(sys.argv)
