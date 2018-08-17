#!/bin/bash

#scp receive.py pi@camera-2.local:RaspberryPi_Scripts

scp $1 pi@camera-2.local:RaspberryPi_Scripts
scp $1 pi@camera-3.local:RaspberryPi_Scripts
scp $1 pi@camera-4.local:RaspberryPi_Scripts
scp $1 pi@camera-5.local:RaspberryPi_Scripts
scp $1 pi@camera-6.local:RaspberryPi_Scripts

