# mqtt-notify
MQTT to Desktop Notification script, for use with [dm8tbr](https://github.com/dm8tbr)'s [mqtt-notify.pl](https://github.com/dm8tbr/irssi-mqtt-notify) [irssi](https://irssi.org/) script.

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

## What
`mqtt-notify.pl` sends irssi's notifications to an [MQTT](https://mqtt.org/) broker (such as [mosquitto](https://mosquitto.org/)). `mqtt-notify.py` takes those messages and turns them into [desktop notifications](https://developer.gnome.org/notification-spec/).

## Why
If irssi runs in [GNU Screen](https://www.gnu.org/software/screen/) or [tmux](https://github.com/tmux/tmux) on a remote system then translating IRC notifications into desktop notifications is not trivial, but some solutions do exist such as [irssi-over-ssh-notifications](https://github.com/equalsraf/irssi-over-ssh-notifications) (which I used successfully for many years). Most of these solutions require that a remote port is forwarded via `ssh -R` to the client to transmit the notifications&mdash;which is fine until you'd like to receive that notification on your phone so you don't miss your team lunch or use [mosh](https://mosh.org/) where port forwarding isn't possible.

## How
`mqtt-notify.py` uses
* [paho](https://www.eclipse.org/paho/) to access the MQTT broker
* [libnotify](https://gitlab.gnome.org/GNOME/libnotify) to make desktop notifications
* [libsecret](https://wiki.gnome.org/Projects/Libsecret) to store and retrieve passwords
* [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/) and [glib](https://gitlab.gnome.org/GNOME/glib/) to run the main loop and track notification closures
 
 ## Setup
`mqtt-notify.py` can be run as a [systemd](https://www.freedesktop.org/wiki/Software/systemd/) user service or started manually.

Setting up an MQTT broker is left as an exercise to the reader. mosquitto is relatively simple to set up. Ensure that you set up `mqtts://` so that your messages are secure in transit (easily done with [Let's Encrypt](https://letsencrypt.org/)). Various guides are available online.

### Installation

```sh
$ mkdir -p ~/bin
$ cp mqtt-notify.py ~/bin
$ mkdir -p ~/.config/systemd/user/
$ cp mqtt-notify.service ~/.config/systemd/user/
```

### Configuration

A simple example configuration file is available at `config`. Copy and modify to suit your needs.
```sh
$ mkdir -p  ~/.config/mqtt-notify/
$ cp config ~/.config/mqtt-notify/
```

#### Password
The user's MQTT authentication password is stored with `libsecret` and will be looked up via the username and the hostname stored in `config`. Add the password to the `libsecret` database.

```sh
$ secret-tool store --label="mqtts://example.com" user myuser service mqtt host example.com
Password: **********
```

### Usage
#### As a user service
```sh
$ systemctl --user daemon-reload
$ systemctl --user enable --now mqtt-notify
```

#### Manual
(Assumes that `~/bin` is in your `$PATH`)

```sh
$ mqtt-notify.py -c ~/.config/mqtt-notify/config
```
