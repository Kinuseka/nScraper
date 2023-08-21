#Standard Library
import sys
import os
import time
import argparse
import logging
import datetime
import json
import re
import pickle
import platform 

#Concurrent/multiple processing libraries
import threading
import anyio
from anyio import TASK_STATUS_IGNORED
from anyio.abc import TaskStatus
#Http request libraries
import urllib
#HTTPX Asynchronous HTTP Requests 
import httpx

#Custom library
import Process
from essentials import updater as Updater
from essentials.Errors import exception as cferror

#EDIT THE MAXIMUM AMOUNT OF DOWNLOAD PROCESS HAPPENING AT THE SAME TIME
#LOWER VALUE: SLOWER, MORE STABLE (BEST IN SLOW NETWORK CONDITIONS)
#HIGHER VALUE: FASTER, LESS STABLE (BEST IN FAST NETWORK CONDITIONS

Process.init_datas()
methods = [
  "cfbypass",
  "mirror"
]

class SortData:
    AcquiredTags = None
    AcquiredPage = None
    AcquiredLinks = None
    TitleName = None
    Download_directory = None
#Error Statistics threshold constants
RETRY_THRESHOLD = 6
PERCENTAGE_THRESHOLD = 0.05

def main(args):
  global run_event
  global Thread1
  logger.info("Parsing arguments")
  responseNumber, returnedData = Process.Data_parse(args) 
  if responseNumber != 0:
    logger.error("%s" % returnedData)
    sys.exit(1)
  logger.info("Getting Data from API")
  #CREATE AN INSTANCE AND LOAD THE NEEDED DATA
  
  Api = Process.CommunicateApi(returnedData)
  AcquiredPage = Api.Pages()
  AcquiredTags = Api.Tags()
  TitleName = Api.Title()[0]
  RawTitleName = Api.Title()[1]
  Dir_name = Api.name
  
  logger.info("Found: %s pages" % AcquiredPage)
  logger.info('Title name: %s' % TitleName)
  logger.info("Acquiring direct links")
  AcquiredLinks = Api.Link_Page(AcquiredPage)
  logger.info("Total of: %s links is loaded" % len(AcquiredLinks))
  logger.info("Setting directory folders")
  if not os.path.isdir("Downloads"):
    os.mkdir("Downloads")
  if not os.path.isdir(os.path.join("Downloads",Dir_name)):
    os.mkdir(os.path.join("Downloads",Dir_name))
  if not os.path.isdir(os.path.join("Downloads",Dir_name,TitleName)):
    Download_directory = (os.path.join("Downloads",Dir_name,TitleName))
    os.mkdir(Download_directory)
  else:
    Download_directory = (os.path.join(os.getcwd(),"Downloads",Dir_name,"%s" % TitleName))
  logger.info("Saving tags data")
  with open(os.path.join(os.getcwd(),"Downloads",Dir_name,TitleName,"metadata.json"),"w") as f:
    t_dict = {}
    t_list = []
    for num,tags in enumerate(AcquiredTags):
      t_list.append(tags)
    origfilename_temp = {"title_original" : RawTitleName}
    gallery_temp = {'gallery_id' : args}
    tags_temp = {"tags" : t_list}
    t_dict.update(origfilename_temp)
    t_dict.update(gallery_temp)
    t_dict.update(tags_temp)
    
    f.write(json.dumps(t_dict))
    
  #Sort Data on a class   
  SortData.AcquiredTags = AcquiredTags
  SortData.AcquiredLinks = AcquiredLinks
  SortData.AcquiredPage = AcquiredPage
  
  SortData.TitleName = TitleName
  SortData.Download_directory = Download_directory
    
  logger.info("Downloading...")
  #RUN STATUS EVENT
  run_event = threading.Event()
  run_event.set()
  Thread1 = threading.Thread(target=statuschecker,args=(verbose,run_event,))
  Thread1.start()
  anyio.run(amain, backend='trio')
  #--+
def statuschecker(verbose,run_event): 
  "User Interface status viewer"
  loggon.info("Status thread opened")
  Links = len(SortData.AcquiredLinks)
  Data_pickledirectory = os.path.join(SortData.Download_directory, ".datadl")
  if os.path.isfile(Data_pickledirectory):
    with open(Data_pickledirectory, "rb") as f: 
        try:
            Process.Data = pickle.load(f)
        except (EOFError, pickle.UnpicklingError, MemoryError):
            pass
  while run_event.is_set():
    time.sleep(0.1)
    #----
    lenned_results = len(Process.VolatileData.response_proc)
    total_bytes = round(Process.VolatileData.total() / 1000000,2)
    progress_bytes = round(Process.VolatileData.progress() / 1000000,2)
    #----
    sys.stdout.write(f"\rDownload in progress [{lenned_results}/{Links}][{progress_bytes}/{total_bytes}]")
    sys.stdout.flush()
    if lenned_results == Links:
      retry_attempts = len(Process.VolatileData.retry_proc)
      #del Process.Data.retry_proc[:]
      #del Process.Data.response_proc[:]
      #Process.Data.total = 0
      #Process.Data.progress = 0
      ready = False
      result = request_status.count(True) == len(request_status)
      unknown_res = request_status.count(2)
      if result:
        print("")
        logger.info("Download completed successfully")
        ready = True
      else:
        print("")
        logger.info("\nDownload failed, some pages did not load correctly")
        if unknown_res:
          logger.warning(f"Some pages encountered unexpected errors. Please report these logs.")
          print(f"Log name: {File}")
        ready = True
      if retry_attempts != 0 and ready:
        percentage = round((retry_attempts/(Links*RETRY_THRESHOLD))*100,2)
        logger.info(f"Retry rate: {retry_attempts}({percentage}%)")
        if retry_attempts >= round((Links*RETRY_THRESHOLD)*PERCENTAGE_THRESHOLD,2):
          logger.warning(f"Retry rates exceed 5% of the acceptable threshold, if you are on a slow network condition, please reduce 'semaphore' variable on 'config.json' to reduce network congestion")
      break
  else:
    print("")
  with open(Data_pickledirectory, "wb") as f:
    data = Process.Data
    pickle.dump(data, f, protocol=4)
  Process.VolatileData.reset()
  Process.Data.reset()
    
async def amain():
  DLInst = Process
  #Regulates max concurrency to be opened
  sem = anyio.Semaphore(max_process_open)
  #Start loop
  async def _collect_status(*args,task_status: TaskStatus = TASK_STATUS_IGNORED):
    status = await DLInst.Queue(*args,task_status)
    request_status.append(status)
  
  async with httpx.AsyncClient() as client, anyio.create_task_group() as tg:
    for num, link in enumerate(SortData.AcquiredLinks):
      loggon.info("Downloading Page %s out of %s" % (num+1, len(SortData.AcquiredLinks)))
      await tg.start(_collect_status, link, num+1, SortData.Download_directory, client, loggon, sem)
      loggon.info("Async: %s has opened successfully" % (num+1))
    else:
      loggon.info("All possible pages has opened successfully")
    loggon.info("Waiting to finish download")
  Thread1.join()
      
if __name__ == "__main__":
  #Status Index
  if sys.version_info[0:2] < (3,6):
    print("UNSUPPORTED VERSION! PLEASE INSTALL PYTHON 3.6 OR HIGHER")
    sys.exit()
  #INITIALIZE FUNCTIONS
  def is_path(string):
    if os.path.isdir(string):
      return string 
    elif os.path.isfile(string):
      return string
    else:
      raise NotADirectoryError(string)
  def sconfig(_type):
    with open("config.json","r") as f:
      config = json.load(f)
    if _type == 1:
      return config["main"]["semaphore"]
    elif _type == 2:
      return config["main"]["Api"]
  def FileName():
    #THIS FUNCTION DELETES OLD LOGFILES, AND ASSIGNS A NAME TO THE NEW ONE
    if not os.path.isdir("Logs"): os.mkdir("Logs")
    list_of_files = os.listdir(os.path.join(os.getcwd(),'Logs'))
    full_path = ["{}".format(os.path.join(os.getcwd(),"Logs",x)) for x in list_of_files]
    if len(list_of_files) == 10:
      oldest_file = min(full_path, key=os.path.getctime)
      os.remove(oldest_file)
    date = str(datetime.datetime.today().replace(microsecond=0)).replace(":",".")
    initial = (os.path.join(os.getcwd(),"Logs","[%s]LogFile") % date)
    if not os.path.isfile("%s.log" % initial):
      return("%s.log" % initial)
  def getSystemInfo(logtype):
    try:
        inf_platform = "System: " + str(platform.system())
        inf_release = "Platform: " + str(platform.release())
        inf_version = "Version: " + str(platform.version())
        inf_machine = "Machine: " + str(platform.machine())
        logtype.info(
        (
        inf_platform,
        inf_release,
        inf_version,
        inf_machine
        )
        )
        return 0
    except Exception as e:
        logging.exception(e)
        return 1
  #Create Custom Loggers
  logger = logging.getLogger(__name__)
  loggon = logging.getLogger("DEV")
  logger.setLevel(logging.DEBUG)
  loggon.setLevel(logging.DEBUG)
  # Create handlers
  File = FileName()
  c_handler = logging.StreamHandler(sys.stdout)
  o_handler = logging.FileHandler(File,mode="a",encoding='utf-8')
  f_handler = logging.FileHandler(File,mode="a",encoding='utf-8')
  c_handler.setLevel(logging.INFO)
  o_handler.setLevel(logging.INFO)
  f_handler.setLevel(logging.INFO)
  # Create format and add it to handlers
  c_format = logging.Formatter('[%(asctime)s]%(levelname)s - %(message)s')
  o_format = logging.Formatter('[%(asctime)s]DEV_%(levelname)s - %(message)s')
  f_format = logging.Formatter('[%(asctime)s]%(levelname)s - %(message)s')
  c_handler.setFormatter(c_format)
  o_handler.setFormatter(o_format)
  f_handler.setFormatter(f_format)
  # Add handlers to the logger
  logger.addHandler(c_handler)
  logger.addHandler(f_handler)
  loggon.addHandler(o_handler)
  #-------
  
  max_process_open = sconfig(1)
  API_DATA_CONFIG = sconfig(2)
  API_MIRROR_ACCOMPLISHED = False
  API_CF_ACCOMPLISHED = False
  EMERGENCY = 255
  verbose = False
  info = '''
  This program will try and scrape images on nhentai.net
  '''
  parser = argparse.ArgumentParser(description=info)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('-n', '--nukecode',metavar=" ", help="-n/--nukecode [argument]")
  group.add_argument('-f', '--filecode',type=is_path, metavar=" ", help="-f/--filecode [file.txt location]")
  group.add_argument('-up', '--update', action="store_true", help="Checks for update and applies it")
  group.add_argument('-v', '--version', action="store_true", help="Show version")
  args = parser.parse_args()
  if args.version:
    print(f"nScraper - V{Updater.ConstructVersion(Updater.CurrentVersion())}")
    print("https://github.com/Kinuseka")
    sys.exit()
  elif args.update:
    if Updater._new_update():
      Updater.show_update(logger,loggon)
      print("Initiating update are you sure? (y/N)",end="")
      __choice_user = input().lower().strip()
      if __choice_user == "y":  
        Updater.upgrade(loggon)
    else:
      print('Version already up to date!')
    sys.exit()
  elif args.filecode:
    logger.warning("This method is still UNDER TESTING and MIGHT NOT WORK PROPERLY")
  request_status = []
  #CALL FUNCTIONS---
      
  
  #Catch error and main function calls
  def callers():
    try:
      Process.initialize(API_DATA_CONFIG) 
      loggon.info(f"=============== System INFO ===============")
      getSystemInfo(loggon)
      loggon.info(f"===========================================")
      if args.filecode:
        FileIterator = Process.CommunicateApi.File_iter(args.filecode)
        if FileIterator:
          time.sleep(3)
          with FileIterator as iof:
            for file_link in iof:
              try:
                logger.info("Downloading link: %s" % file_link)
                main(file_link)
              except (urllib.error.HTTPError, cferror.NotFound) as e:
                if e.code == 404:
                  logger.error("The content you are looking for is not found")
                else:
                  raise e
              finally:
                print("-"*10)
        else:
          logger.error("This method is not available for the current module")
      else:
        main(args.nukecode)
    except (urllib.error.HTTPError, cferror.NotFound, cferror.NetworkError) as e:
      #ONLY OCCURS WHEN THERE IS NO RESULTS
      if e.code == 404:
        logger.error("The content you are looking for is not found")
      else:
        logger.error("HTTP Error Code: %s" % e.code)
        if API_DATA_CONFIG["cf_bypass"] and not API_CF_ACCOMPLISHED:
          return 102
        elif API_DATA_CONFIG["mirror_available"] and not API_MIRROR_ACCOMPLISHED:
          return 101
      sys.exit(1)
    except (urllib.error.URLError, cferror.NetworkError) as error:
      logger.error("A connection error has occured")
      loggon.exception("Exception catched: %s" % sys.exc_info()[0])
      sys.exit(1)
    except SystemExit as error:
      if error.code == EMERGENCY:
        os._exit(1)
      else:
        raise
    except KeyboardInterrupt:
        print("")
        logger.info("Attempting to close thread..")
        run_event.clear()
        Thread1.join()
        logger.info("Thread closed successfully")
    except ModuleNotFoundError as error:
      mod_dir =  f'Lib.{API_DATA_CONFIG["module_name"]}'
      if error.name == mod_dir:
        if API_MIRROR_ACCOMPLISHED:
          logger.error("Mirror server is not available, traceback is saved on the recent log file")
          loggon.exception("Exception catched: %s" % sys.exc_info()[0])
        else:
          logger.error(f"Importing error, {error.name} is not a valid module, traceback is saved on the recent log file")
          loggon.exception("Exception catched: %s" % sys.exc_info()[0])
    except:
      logger.error("An unknown error was found while getting data from API, traceback is saved on the recent log file")
      loggon.exception("Exception catched: %s" % sys.exc_info()[0])
      sys.exit()
  threading.Thread(target=Updater.init,daemon=True).start()
  while True:
    exit_code = callers()
    if exit_code == 102 and not API_CF_ACCOMPLISHED:
      logger.info("Trying to bypass CF")
      API_DATA_CONFIG["module_name"] = f'{API_DATA_CONFIG["module_name"]}_cf'
      API_CF_ACCOMPLISHED = True
    elif exit_code == 101 and not API_MIRROR_ACCOMPLISHED:
      logger.info("Mirror server enabled, trying mirror server.")
      API_DATA_CONFIG["module_name"] = f'{API_DATA_CONFIG["module_name"]}_mirror'
      API_MIRROR_ACCOMPLISHED = True
    else:
      break
  Updater.show_update(logger, loggon)
    
