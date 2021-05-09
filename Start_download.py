import Process
import Lib
import sys
import threading
import os
import argparse
import logging
import datetime
import requests
import json
import time
def FileName():
  #THIS FUNCTION DELETES OLD LOGFILES, AND ASSIGNS A NAME TO THE NEW ONE
  if not os.path.isdir("Logs"): os.mkdir("Logs")
  list_of_files = os.listdir(os.path.join(os.getcwd(),'Logs'))
  full_path = ["{}".format(os.path.join(os.getcwd(),"Logs",x)) for x in list_of_files]
  if len(list_of_files) == 10:
    oldest_file = min(full_path, key=os.path.getctime)
    os.remove(oldest_file)
  date = datetime.datetime.today().replace(microsecond=0)
  initial = (os.path.join(os.getcwd(),"Logs","[%s]LogFile") % date)
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

verbose = False
info = '''
This program will try and scrape images on nhentai.net
'''
parser = argparse.ArgumentParser(description=info)
parser.add_argument('-n', '--nukecode',metavar=" ", help="-n/--nukecode [argument]",required=True)
parser.add_argument('-v', '--verbose', action="store_true", help="Enable a verbose downloader")
args = parser.parse_args()
if args.verbose:
  verbose = True
args = args.nukecode
def main():
  global Api 
  global AcquiredPage
  global AcquiredTags
  global AcquiredLinks
  global TitleName
  global Download_directory
  logger.info("Parsing arguments")
  responseNumber, returnedData = Process.Data_parse(args) 
  if responseNumber != 0:
    logger.error("%s" % returnedData)
    sys.exit()
  logger.info("Getting Data from API")
  try:
    #CREATE AN INSTANCE AND LOAD THE NEEDED DATA
    Api = Process.CommunicateApi(returnedData)
  except Lib.Exceptions.SearchNotFound as error:
    logger.error("Exception: SearchNotFound detected. Invalid gallery is given")
    loggon.exception("Exception catched: %s" % sys.exc_info()[0])
    sys.exit()
  except requests.exceptions.ConnectionError as error:
    logger.error("A connection error has occured")
    loggon.exception("Exception catched: %s" % sys.exc_info()[0])
    sys.exit()
  except:
    logger.error("An unknown error was found while getting data from API, traceback is saved on the recent log file")
    loggon.exception("Exception catched: %s" % sys.exc_info()[0])
  AcquiredPage = Api.Pages()
  AcquiredTags = Api.Tags()
  TitleName = Api.Title()
  logger.info("Found: %s pages" % AcquiredPage)
  logger.info('Title name: "%s"' % TitleName)
  logger.info("Acquiring direct links")
  AcquiredLinks = Api.Link_Page(AcquiredPage)
  logger.info("Total of: %s links is loaded" % len(AcquiredLinks))
  logger.info("Setting directory folders")
  if not os.path.isdir("Downloads"):
    os.mkdir("Downloads")
  if not os.path.isdir(os.path.join("Downloads",TitleName)):
    Download_directory = (os.path.join("Downloads",TitleName))
    os.mkdir(Download_directory)
  else:
    Download_directory = (os.path.join(os.getcwd(),"Downloads","%s" % TitleName))
  logger.info("Saving tags data")
  try:
    with open(os.path.join(os.getcwd(),"Downloads",TitleName,"metadata.json"),"w") as f:
      f.write(json.dumps({'gallery_id' : args}))
      f.write("\n")
      for tags in AcquiredTags:
        tags = json.dumps(tags)
        f.write(tags)
        f.write("\n")
  except:
    logger.error("An error has occured, check logs and report to dev")
    loggon.exception("")
    logger.info("Downloading...")

#Download zone
finish_process = []
def statuschecker(verbose): 
  verbose_value = 0
  Links = len(AcquiredLinks)
  while True:
    time.sleep(0.1)
    results = Process.results
    lenned_results = len(results)
    average = 0
    for key in Process.current:
      average += Process.current.get(key,0).get("speed",0)
    maxaverage = round(average,2)
    average = round((average/5),2)
    if verbose == True:
      verbose_value += 1
      Processes = Process.current
      sys.stdout.write("\r Thread1: %s || Thread2: %s || Thread3: %s || Thread4: %s || Thread5: %s" % (Processes["File1"]["speed"],Processes["File2"]["speed"],Processes["File3"]["speed"],Processes["File4"]["speed"],Processes["File5"]["speed"]))
      if verbose_value == 60:
        verbose_value = 0
        print("")
        sys.stdout.write("Download in progress [%s/%s] %s%s || Current: %sKB/s || Max: %sKB/s" % (lenned_results,Links,round(100 * lenned_results / Links,2),"%",average,maxaverage))
        print("")
    else:
      maxlabel = "MB/s" if (maxaverage >= 1000) else "KB/s"
      maxaverage = round((maxaverage/1000),2) if (maxaverage >= 1000) else maxaverage
      avelabel = "MB/s" if (average >= 1000) else "KB/s"
      average = (round((average/1000),2)) if (average >= 1000) else average 
      avename = ("%s%s" % (average,avelabel))
      maxname = ("%s%s" % (maxaverage,maxlabel))
      sys.stdout.write("\r[Download in progress [%s/%s] %s%s || Current: %s || Max: %s]" % (lenned_results,Links,round(100 * lenned_results / Links,2),"%",avename,maxname))
    sys.stdout.flush()
    if lenned_results >= Links:
      print("")
      logger.info("Download has been completed")
      finish_process.append("Done")
    
def download():
  Thread1 = threading.Thread(target=statuschecker,args=(verbose,))
  Thread1.daemon = True
  Thread1.start()
  loggon.info("Status thread opened")
  #Start loop
  assigned = 0
  while True:
    for num, link in enumerate(AcquiredLinks):
      loggon.info("Downloading Page %s out of %s" % (num+1, len(AcquiredLinks)))
      #Regulates maximum threads to be opened 
      while True:
        assigned += 1
        if assigned == 6:
          assigned = 1
        if Process.current[f"File%s" % assigned]["status"] == True:
          continue
        break
      ##while threading.active_count() == 8: pass
    #Slows down thread creation to prevent memory overlap
      
      Thread2 = threading.Thread(target=Api.Download, args=(link,num+1,Download_directory, assigned))
      Thread2.daemon = True
      Thread2.start()
      loggon.info("Thread: %s has opened successfully" % assigned)
    else:
      loggon.info("All possible threads has opened successfully")
      loggon.info("Waiting for downloader")
    while not "Done" in finish_process: continue
    sys.exit()

main()
download()