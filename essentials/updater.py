#Author: Kinuseka (https://github.com/Kinuseka)
"This module checks for updates"

import requests
import json
import os
import sys
import time

# Configurations
LOCAL_DIR = os.getcwd()
class UpdateInformation:
    Name_ver = "nhScraper"
    Version_Host = "https://raw.githubusercontent.com/Kinuseka/Kinuseka.github.io/main/external%20resource/upd_nh.json"
    Current_Version: list = [0,6,0] 
    Version: list = None
    Message: str = None
    Additional: dict = None
    #Library Versioning
    A_MaV = 0
    A_MiV = 0
    A_PaV = 0
    A_Mes = None
    #Internal process checks
    initialized = False
    init_error = None

def init():
    try:
        req = requests.get(UpdateInformation.Version_Host)
        data = req.json()[UpdateInformation.Name_ver]
        version = data['Version']
        if data.get('Message', None):
            UpdateInformation.Message = data['Message']
        if data.get('Additional', None):
            UpdateInformation.Additional = data['Additional']
        if data.get('Version', None):
            UpdateInformation.Version = data['Version']
        UpdateInformation.initialized = True
    except Exception as e:
        UpdateInformation.init_error = e

def Version():
    return UpdateInformation.Version

def CurrentVersion():
    return UpdateInformation.Current_Version

def ConstructVerion(Version: list):
    return f"{Version[0]}.{Version[1]}.{Version[2]}"

def Comparator(version, remote):
    ftr,new = False, False
    for cur_ver, rem_ver in zip(version, remote):
        if cur_ver < rem_ver:
            new = True
        if cur_ver > rem_ver:
            ftr = True
    return new, ftr

def show_update(logger, loggon):
    for t in range(0,5):
        if UpdateInformation.initialized:
            break
        elif UpdateInformation.init_error:
            loggon.exception(f'Error occured on fetching host details. Host: {UpdateInformation.Version_Host}')
            return
        time.sleep(1)
    else: 
        loggon.error(f'Could not fetch update details from: {UpdateInformation.Version_Host}')
        return
    new_update, future_update = Comparator(UpdateInformation.Current_Version, UpdateInformation.Version)
    if new_update:
        logger.info(f"New update found: v{ConstructVerion(Version())}")
    elif future_update:
        logger.warn("This version is from the future, might be unstable.")
        logger.info(f"Available: v{ConstructVerion(Version())} | Your version: v{ConstructVerion(CurrentVersion())}")
    message = UpdateInformation.Message
    if all((new_update, message)) or all((future_update, message)):
        logger.info(f'[Announce]: {message}')

def _new_update():
    init()
    n, f = Comparator(UpdateInformation.Current_Version, UpdateInformation.Version)
    if n: return True
    return False

if __name__ == "__main__":
    class Printer:
        def info(mess):
            print(mess)
        def warn(mess):
            print(f"[warn] {mess}")
    init()
    show_update(Printer)