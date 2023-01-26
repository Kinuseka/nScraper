from functools import wraps
import anyio
import httpx
import Lib
import sys
import os
import time
import re


def initialize(API_DATA_CONFIG):
  Lib.init_import(API_DATA_CONFIG["module_name"])

def Data_parse(data):
  """For MODDERS:
  1.If you want to add a Link verifier to prevent invalid link error then you have nothing to edit here, however you can modify it to return true all the time if you dont want this feature
  2.You can modify the 1st condition on line 18 if the target site does not support or does not use numbers to identify their gallery. 
  3.If you want to use links, be sure that the user has to include http:// or https:// to prevent further problems. 
  The Lib.Checklink is connected to Lib/NHentai.py (In Default)
  """
  if data.isdigit():
    data = Lib.CheckLink(data, digit=True)
    return(0,data)
  elif "http://" in data or "https://" in data:
    result,data = Lib.CheckLink(data)
    return(result,data)
  else:
    return(1,"A link should have http:// or https://")


def validatename(func):
  """Info:
  Use this as a wrapper to prevent filename complication such as;
  "/" is normally used to differentiate directory
  "\\" similar usage but for windows.
  (Note I used double backslash in source code to escape the backslash character. Read about it: https://www.w3schools.com/python/gloss_python_escape_characters.asp)
  if both of these are present, the program might confuse it for a different directory rather than treating it as a file name.
  
  Use this wrapper to modify forbidden filenames from windows system
   The following reserved characters:

        < (less than)
        > (greater than)
        : (colon)
        " (double quote)
        / (forward slash)
        \ (backslash)
        | (vertical bar or pipe)
        ? (question mark)
        * (asterisk)
  """
  @wraps(func)
  def wrapper(self):
    word_orig = func(self)
    word = word_orig
    forbidden = ['<', '>', ':', '"', "|", "?", "*"]
    for char in forbidden:
      word = word.replace(char, "")
        
    word = word.replace("\\","_")
    word = word.replace("/","_")
    
    
    return (word,word_orig)
  return wrapper

def sorttags(func):
  """:
    Use this Wrapper to sort your tags.
    """
  @wraps(func)
  def wrapper(self):
    #Start here
    tags = func(self)
    return tags
  return wrapper

class CommunicateApi:
  """Info:
  Used for the __main__ to communicate with the NHentai.py(In default).
  Usually does not require modifying this unless if you want to add missing features
  """
  def __init__(self, data):
      
      self._Handler = Lib.Api(data)
      self.name = self._Handler.name
  def Pages(self):
    data = self._Handler.Pages()
    return data
  @sorttags #Wrapper that will sort tags
  def Tags(self):
    """If the tags are all over the place, you can use 'sorttags' wrapper to create a tag sorting algorithm to keep the tags clean sorted.
    """
    data = self._Handler.Tags()
    return data
  @validatename #Wrapper that modify an invalid name
  def Title(self):
    data = self._Handler.Title()
    return data
  def Link_Page(self,var):
    """Info:
    If 'var' is 20 then it should return Page links from 1 to 20
    'var' is dependent on how many links should be returned for example: var = 20, Return ['https://site.example/page1.jpg',2,3...'https://site.example/page20.jpg']
    
    Link_Page is connected to Api.Direct_link on Lib
    """
    data_list = [self._Handler.Direct_link(x) for x in range(1,(int(var)+1))]
    return data_list
  def File_iter(data):
    return Lib.Iterdata(data)

async def Queue(link,title_value,location,client,loggon,sem,task_status):
  async def __start_process():
    """Info:
    This is the main downloader of the program
    It uses asynchronous functions download multiple pages at the same time. It has a timeout of up until 6 fails before stops completely to free up resources and bandwidth to the next Page to be downloaded Queued by the anyio.Semaphore()
    link - Downloadable link to the file 
    title_value - Page file number
    location - Location to save the page 
    client - Httpx AsyncClient object
    loggon - Logger to log status on a log file (For Debugging purposes) 
    sem - Semaphore object
    task_status - TaskGroup object. call task_status.started() to start another Task. Failure to call the method will cause the program to fail.
    """
    """
    Download a file from the given URL and save it to the specified save path.
    If there is a failure, the function will retry the download up to MAX_RETRIES times.
    If the download was interrupted, it will continue from the last downloaded byte
    """
    #Functions
    async def _get_head(client,link: str, return_err: bool = False, attempts: int = 5):
      redo = 0
      recent_exp = None
      while not redo >= attempts:
        try:
          return await client.head(link)
        except httpx.HTTPError as e:
          redo += 1
          recent_exp = e
          loggon.exception(f'Error collecting header {redo}/{attempts}')
      else:
        raise recent_exp if recent_exp else AttributeError('Error had occured but cannot find the error')
    def _check_if_done(Data: dict):
      "Check early if the progress is on dump and the file exists. This function is important to reduce strain on the remote server"
      try:
        dl_path = Data.progress_status[title_value]["directory"]
        if os.path.getsize(dl_path) == Data.progress_status[title_value]["Max"]:
          return True
        os.remove(dl_path)
        return False
      except FileNotFoundError:
        return False
      except KeyError:
        return False
    def _no_data_check(size: int, downloaded: int):
      "Check the current state of the data received and the actual data got, this is an important function to identify the currect action needed"
      if downloaded == size:
        return 0
      elif downloaded < size:
        return 1
      elif downloaded > size:
        return 2
    def _invoke_finish(cond: bool):
      Data.progress_status[title_value]["bool"] = cond
      VolatileData.response_proc.append(cond)
    task_status.started() #This starts the child process
    #Before start, check if download gas occured before
    if _check_if_done(Data):
      _invoke_finish(True)
      return True
    #Set initial values
    MAX_RETRIES = 6
    retries = 0
    headers = {}
    downloaded_size = 0
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
    # print(location)
    #Load client
    async with httpx.AsyncClient() as client:
      #Get headers
      try:
        #If dump is loaded
        download_path =  os.path.normpath(Data.progress_status[title_value]["directory"])
        downloaded_ondata_max = Data.progress_status[title_value]['Max']
        downloaded_ondata_current = Data.progress_status[title_value]['Bytes']
        downloaded_size = os.path.getsize(download_path) if os.path.exists(download_path) else 0
        #Synchronize Dump from actual file size
        if downloaded_size != downloaded_ondata_current:
          Data.progress_status[title_value]['Bytes'] = downloaded_size
          downloaded_ondata_current = downloaded_size
        _action_type =  _no_data_check(downloaded_ondata_max, downloaded_ondata_current)
      except KeyError:
        #If dump does not exist
        #Get headers
        resp = await _get_head(client, link)
        resp.raise_for_status()
        #Preload progress
        Data.progress_status[title_value] = {"bool":False,"Bytes":0,"Max":False}
        #Get header content
        format_file = resp.headers.get('Content-Type').replace("image/","")
        file_name = ("%s.%s" % (title_value, format_file))
        download_path = os.path.join(os.getcwd(),location,file_name)
        Data.progress_status[title_value]["directory"] = download_path
        #Configure loaded data
        save_path = os.path.join(location,file_name)
        downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
        _action_type =  _no_data_check(int(resp.headers.get('content-length', 0)), downloaded_size)
      #Initialize data
      loggon.info(f'Action required code: {_action_type}')
      if _action_type == 0:
        Data.progress_status[title_value]["Max"] = downloaded_size
        Data.progress_status[title_value]["Bytes"] = downloaded_size
        _invoke_finish(True)
        return True
      elif _action_type == 1:
        pass
      elif _action_type == 2:
        #Reset download due to override
        os.remove(download_path)
      Data.progress_status[title_value]["Max"] = downloaded_size
      headers['Range'] = f"bytes={downloaded_size}-"
      headers = {}
      #====
      while retries <= MAX_RETRIES:
          Data.progress_status[title_value]["Max"] = downloaded_size
          try:
              async with client.stream('GET', link, headers=headers) as response:
                response.raise_for_status()
                response_code = response.status_code
                #Check expected response code
                if response_code < 300 and response_code >= 200:
                  if response_code not in (200,206):
                      loggon.warn(f"<{title_value}> Unexpected SUCCESSFUL HTTP response code: {response_code}")
                else:
                  loggon.error(f"<{title_value}> Unexpected http response code: {response_code}")
                  continue
                async with await anyio.open_file(download_path, "ab") as asf:
                    # check if the file is partially downloaded
                    if response.headers.get("Content-Range"):
                        loggon.info(f"Resuming download from byte {downloaded_size}")
                    #Log all progress
                    max_size = int(response.headers.get("Content-Length", 0))
                    total_size = max_size + downloaded_size
                    Data.progress_status[title_value]["Max"] += max_size         
                    Data.progress_status[title_value]["Bytes"] = total_size
                    async for chunk in response.aiter_bytes():
                        downloaded_size += len(chunk)
                        Data.progress_status[title_value]["Bytes"] = downloaded_size
                        await asf.write(chunk)
                loggon.info(f"Downloaded {downloaded_size} of {total_size} bytes")
                _invoke_finish(True)
                return True
          except httpx.HTTPError as e:
            retries += 1
            #Retry 0-[max retries] times
            if retries < 7:
              loggon.exception(f"\nP:{title_value},Error: {e}, full data on logs")
              loggon.info(f"<{title_value}>Problem occured, retrying {retries}/6")
              VolatileData.retry_proc.append(True)
              await anyio.sleep(1)
              continue
            Data.progress_status[title_value]["bool"] = False
            VolatileData.response_proc.append(False)
            loggon.exception("DLException: ")
            _invoke_finish(False)
            return False
      else:
        _invoke_finish(False)
        return False 
  async with sem: 
    return await __start_process()
    
#del Process.Data.retry_proc[:]
      #del Process.Data.response_proc[:]
      #Process.Data.total = 0
      #Process.Data.progress = 0

class Data_raw:
  def __init__(self):
    self.progress_status = {}

  def reset(self):
    self.progress_status = {}
class VData:
  def __init__(self):
    self.response_proc = []
    self.retry_proc = [] 
    self.data = Data
  
  def total(self):
    Max = 0
    for n in list(Data.progress_status):
      Max += Data.progress_status[n]["Max"]
    return Max 
    
  def progress(self):
    Bytes = 0
    for n in list(Data.progress_status):
      Bytes += Data.progress_status[n]["Bytes"]
    return Bytes
  
  def reset(self):
    self.response_proc = []
    self.retry_proc = [] 
    self.data = Data
  
def reset_datas():
  global Data
  global VolatileData
  try:
    Data = Data.reset()
    VolatileData = VolatileData.reset()
  except AttributeError:
    pass
def init_datas():
  global Data
  global VolatileData
  Data = Data_raw()  
  VolatileData = VData()

if __name__ == "__main__":
  pass
