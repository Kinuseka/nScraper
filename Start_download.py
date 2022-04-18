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

#EDIT THE MAXIMUM AMOUNT OF DOWNLOAD PROCESS HAPPENING AT THE SAME TIME
#LOWER VALUE: SLOWER, MORE STABLE (BEST IN SLOW NETWORK CONDITIONS)
#HIGHER VALUE: FASTER, LESS STABLE (BEST IN FAST NETWORK CONDITIONS

class SortData:
    AcquiredTags = None
    AcquiredPage = None
    AcquiredLinks = None
    TitleName = None
    Download_directory = None
    

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
  TitleName = Api.Title()
  Dir_name = Api.name
  
  logger.info("Found: %s pages" % AcquiredPage)
  logger.info('Title name: "%s"' % TitleName)
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
    t_dict = []
    gallery_temp = {'gallery_id' : args}
    t_dict.append(gallery_temp)
    for num,tags in enumerate(AcquiredTags):
      t_dict.append(tags)
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
        except (EOFError,pickle.UnpicklingError):
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
      if result:
        print("")
        logger.info("Download completed successfully")
        ready = True
      else:
        print("")
        logger.info("\nDownload failed, some pages did not load correctly")
        ready = True
      if retry_attempts != 0 and ready:
        percentage = round((retry_attempts/(Links*6))*100,2)
        logger.info(f"Retry rate: {retry_attempts}({percentage}%)")
        if retry_attempts >= round((Links*5)*0.05,2):
          logger.warning(f"Retry rates exceed 5% of the acceptable threshold, if you are on a slow network condition, please reduce 'semaphore' variable on 'config.json' to reduce network congestion")
      break
  else:
    print("")
  with open(Data_pickledirectory, "wb") as f:
    data = Process.Data
    pickle.dump(data, f, protocol=4)
        
    
    
    
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
    print(initial)
    if not os.path.isfile("%s.log" % initial):
      return("%s.log" % initial)
  #Create Custom Loggers
  logger = logging.getLogger(__name__)
  loggon = logging.getLogger("DEV")
  logger.setLevel(logging.DEBUG)
  loggon.setLevel(logging.DEBUG)
  # Create handlers
  File = FileName()
  c_handler = logging.StreamHandler(sys.stdout)
  o_handler = logging.FileHandler(File)
  f_handler = logging.FileHandler(File)
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
  EMERGENCY = 255
  verbose = False
  info = '''
  This program will try and scrape images on nhentai.net
  '''
  parser = argparse.ArgumentParser(description=info)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('-n', '--nukecode',metavar=" ", help="-n/--nukecode [argument]")
  group.add_argument('-f', '--filecode',type=is_path, metavar=" ", help="-f/--filecode [file.txt location]")
  parser.add_argument('-v', '--verbose', action="store_true", help="Enable a verbose downloader")
  args = parser.parse_args()
  if args.verbose:
    verbose = True
  request_status = []
  #CALL FUNCTIONS---
      
  
  #Catch error and main function calls
  try: 
    if args.filecode:
      if Process.CommunicateApi.File_iter.available:
        
        logger.warning("This method is still UNDER TESTING and MIGHT NOT WORK PROPERLY")
        time.sleep(3)
        with Process.CommunicateApi.File_iter(args.filecode) as iof:
          for file_link in iof:
            logger.info("Downloading link: %s" % file_link)
            main(file_link)
            print("-"*10)
      else:
        logger.error("This method is not available for the current module")
    else:
      main(args.nukecode)
  except urllib.error.HTTPError as e:
    #ONLY OCCURS WHEN THERE IS NO RESULTS
    if e.code == 404:
      logger.error("The content you are looking for is not found")
    else:
      logger.error("HTTP Error Code: %s" % e.code)
      
    sys.exit(1)
  except urllib.error.URLError as error:
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
  except:
    logger.error("An unknown error was found while getting data from API, traceback is saved on the recent log file")
    loggon.exception("Exception catched: %s" % sys.exc_info()[0])
    sys.exit()