Installation

- pip3 install flask
- pip3 install flask_socketio
- pip3 install hidapi

copy 80-ps2-buzzer.rules to /etc/udev/rules.d/ and change GROUP if necessary. Re-insert USB PS2 buzzer afterwards

run with python3 buzzer.py and open webbrowser http://localhost:8000

You can also run this on a headless raspberry pi (see dhcpd.conf and hostapd.conf for dhcp server and wifi access point).