#Author: Kinuseka (https://github.com/Kinuseka)
"This module checks for updates"

import __main__
import requests
import json
import os
import sys
import time
import subprocess
import zipfile
import io
import shutil
from pathlib import Path
from pathlib import PurePath
import hashlib

# Configurations
LOCAL_DIR = os.getcwd()
class UpdateInformation:
    Name_ver = "nhScraper"
    Version_Host = "https://raw.githubusercontent.com/Kinuseka/Kinuseka.github.io/main/external%20resource/upd_nh.json"
    Current_Version: list = [0,6,1] 
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

def git_method(logger=None):
    def _sub_processor(process):
        for line, errl in zip(process.stdout, process.stderr):
            print(line.strip(), errl.strip())
            if logger:
                logger.info(line.strip())
                logger.info(errl.strip())
    def _result_judge(process):
        process.wait()
        if process.returncode == 0:
            # Git command executed successfully
            return True, None
        else:
            return False, process.stderr
    properdir = Path(__main__.__file__).parent.resolve()
    process = subprocess.Popen(['git','pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=properdir)
    _sub_processor(process)
    result, err = _result_judge(process)
    if not result:
        return False
    #if success then proceed to step 2
    version_str = ConstructVerion(Version())
    process = subprocess.Popen(['git','checkout',version_str], stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True, cwd=properdir)
    _sub_processor(process)
    result, err = _result_judge(process)
    print(err)
    if not result:
        return False
    return True #update success
def md5_for_file(f, block_size=2**20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()
def merge(path: Path, into: Path):
    """Copies path to into, recursing into children (if path is a directory) and ignoring already existing files."""
    if not path.exists():
        raise ValueError(path, "doesn't exist")
    if path.is_dir():
        # then we copy all children
        into.mkdir(exist_ok=True, parents=True)
        for child in path.iterdir():
            merge(child, into / child.name)
    else:
        # a file we just try to copy
        if into.exists():
            if md5_for_file(open(into,'rb')) == md5_for_file(open(path,'rb')):
                print("No changes on file: ", into)
            else:
                print("Changes found on file: ", into)
                shutil.copy2(path, into)
            return
        shutil.copy2(path, into)
def zip_method(logger=None):
    print("Using zip method")
    version_str = ConstructVerion(Version())
    api_url = f'https://api.github.com/repos/Kinuseka/nScraper/releases/tags/{version_str}'
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            # Parse the JSON response
            release_data = response.json()
            # Get the source code zipfile URL from the release data
            zipfile_url = release_data['zipball_url']
            # Download the zipfile
            print(f"Downloading... [{api_url}]")
            response = requests.get(zipfile_url)
            response.raise_for_status()
            buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(buffer, 'r') as zip_ref:
                properdir = Path(__main__.__file__).parent.resolve()
                temp_folder = os.path.join(properdir,'.cache')
                zip_ref.extractall(path=temp_folder)
                for croot, cdir, cfile in os.walk(temp_folder):
                    #Inside .cache
                    updatedPath = Path(PurePath(croot,cdir[0]))
                    merge(updatedPath, properdir)
                    break
                    # for iroot, idir, ifile in os.walk(os.path.join(croot,cdir[0])):
                    #     print(idir, iroot, ifile)
                    #     #This part should be inside the folder
                    #     for roots, dirs, files in os.walk(idir[0]):
                    #         for file in files:
                    #             direct = PurePath(roots, file)
                    #             dest = PurePath(temp_folder, direct.name)
                    #             print("Checking: ", direct, dest)
                    #             shutil.move(direct, dest)
                    #         for dir in dirs:
                    #             direct = PurePath(roots, dir)
                    #             dest = PurePath(temp_folder, direct.name)
                    #             print("Checking: ", direct, dest)
                    #             merge(Path(direct), Path(dest))
                    #     break
                    # break
            shutil.rmtree(temp_folder)
            print("Update Successful")
            return True
        else:
            print("Api rejected, ", response.text)
            return False
    
    except Exception as e:
        if logger:
            logger.exception("Error on updater:")
        print("Error occured while updating, ", e)
        return False

def upgrade(logger=None):
    n, f = Comparator(UpdateInformation.Current_Version, UpdateInformation.Version)
    if n: 
        # status = git_method(logger)
        status = zip_method(logger)
        if not status:
            # status = zip_method(logger)
            # status = False
            # if status:
            #     return True
            # else:
            #     print("Update was not successful")
            #     return False
            print("Update was not successful")
            return False
        else:
            return True
    print("There was no update found. An error in logic probably occured in the updater.")
    return False

if __name__ == "__main__":
    class Printer:
        def info(mess):
            print(mess)
        def warn(mess):
            print(f"[warn] {mess}")
    init()
    show_update(Printer)