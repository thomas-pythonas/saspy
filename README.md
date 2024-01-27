# SASPY
Slots Accounting System (SAS) Protocol is a standard when comes to Slot Machine and VLTs.

## How To
```bash
$ git clone https://github.com/zacharytomlinson/saspy.git
$ cd saspy
$ pip install -r requirements.txt
$ nano config.yml # Adjust according your needs
$ python example.py
```

# Notes
## Raspberry Hardware Limitation
As per SAS documentation, for the connection, you need:
> 19.2 KBaud in a "wakeup" mode. The 11-bit data packet consists of one start bit, eight data bits, a
> ninth ‘wakeup’ bit, and one stop bit.

#### Connecting with RPI 3 B+:
1) Update your machine:
```
user@host> sudo apt-get update
user@host> sudo apt-get dist-upgrade
user@host> sudo apt-get clean
```
2) Enable UART in config and disable bluetooth
```
sudo echo "enable_uart=1" >> /boot/config.txt
sudo echo "dtoverlay=pi3-disable-bt" >> /boot/config.txt
```
3) Reboot for changes to take effect 
``` 
sudo echo reboot
```
4) Configure serial connection to "serial0" port in config.yml
```
connection:
  serial_port: /dev/serial0
```
#### Connecting with RPI 4:

#### Connecting with USB to serial adapter, use a usb rs232 cable.....I used this [one](https://www.amazon.com/USB-Serial-Adapter-Prolific-PL-2303/dp/B00GRP8EZU/ref=sr_1_1_sspa?dib=eyJ2IjoiMSJ9.eT7IwLbFTyi5P6wiZqvnXrIsQpdtfPz_M46xtQa_S1I6h-lpFonAvq5YC5xJqm4vO8e3APmv6ZveRIHnEk3JvZ7RPORl8CFQWSUM226Dz0JssJAFQzWxU_Rk-YZaVXY5yPT9ZX-bqG0CDKUEzPruTJWEFg-ITUZtUOwr8KLTrvxvVg-ounmiZNAaizmQvxjrTdVozOF4iRbI5UF54oqfyn1obbD9whyaS_eGnl-TRcU.CRPZSqj6-D9E9pUJExtcBxGZd89oO6OAewGmvDxATTU&dib_tag=se&keywords=prolific%2Busb%2Bto%2Bserial&qid=1705598420&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1).
## Good to know
### Event Reporting
Basically you have 2 ways: ***Standard event poll*** and ***real time event poll***.

The **standard event poll** works with a FIFO memory and in real world use cases is kinda useless (unless you need to store the history of this machine status). You can call this event simply using the `event_poll` method in the code.

When you start the **real time event reporting** the machine, no matter what you ask, will always reply with the current event in the machine...leading to badcrc error and whatnot...plus the real time event responses are not mapped in the code (don't worry...im working on it). The function, in the code, to enable this is `en_dis_rt_event_reporting`.

Of course i needed the real time event reporting (to bind some actions) and at same time use some of the `aft_*` functions in the code.

To solve this issues i had to use the operator page on the machine to enable a second channel and buy a second prolific usb rs232 cable....

In this way on a channel i enabled the real time event reporting and on the second channel i could use the script normally (and the AFT functions) without problems.....

Of course...this is a way created out of "no time"....if somebody has a better idea im all ear !

## Dictionaries Notes
### GPOLL
**"4f": "Bill accepted"** 
- Non-RTE mode: use this for all bills without explicit denomination. 
- RTE mode: use for all bill denominations.

**"50": "$200.00 bill accepted"**
- Non-RTE only

# Authors
This project was initiated by [thomas-pythonas](https://github.com/thomas-pythonas) in 2018 and has no update since then.

Current author and mantainer are:

- [zacharytomlinson](https://github.com/zacharytomlinson)
- [well-it-wasnt-me](https://github.com/well-it-wasnt-me)