from functools import wraps
import anyio
import httpx
import Lib
import sys
import os
import time
import re


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
    def __complete_return():
        VolatileData.response_proc.append(True)
        Data.progress_status[title_value]["bool"] = True
        return True
    def __complete_resume():
        
        #Data.progress_status[title_value]["bool"] = bool
        try:
            if os.path.getsize(download_path) == Data.progress_status[title_value]["Max"]:
                VolatileData.response_proc.append(True)
                return True
            os.remove(download_path)
            return False
        except FileNotFoundError:
            return False
    def __incomplete_return():
        VolatileData.response_proc.append(False)
        Data.progress_status[title_value]["bool"] = False
        return False
    def __incomplete_resume():
        try:
            if os.path.getsize(download_path) == Data.progress_status[title_value]["Bytes"]:
                return True
            os.remove(download_path)
            return False
        except FileNotFoundError:
            return False
        
    def __reset_progress():
        Data.progress_status[title_value] = {"bool":False,"Bytes":0,"Max":False}
    file = title_value
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}
    download_path = ""
    
    continued = False
    manual_fix = False
    #start = time.process_time()
    timeout = 0
    Data_psnap = 0
    Data_tsnap = 0
    
    task_status.started() #Task is ready
    
    try:
      if Data.progress_status[title_value]["bool"]:
        download_path =  os.path.normpath(Data.progress_status[title_value]["directory"])
        if __complete_resume():
            return True
        else:
            __reset_progress()
      elif Data.progress_status[title_value]["Max"]:
        download_path =  os.path.normpath(Data.progress_status[title_value]["directory"])
        Data_tsnap = Data.progress_status[title_value]["Max"] 
        Data_psnap = Data.progress_status["Bytes"]
        if __incomplete_resume():
            headers["Range"] = "bytes=%d-" % Data_psnap
        else:
            __reset_progress()
        continued = True 
    except KeyError as e: 
      Data.progress_status[title_value] = {"bool":False,"Bytes":0,"Max":False}
        
    while True:
      try:
        #Downloader
        async with client.stream('GET',link,headers=headers) as resp:
          
          format_file = resp.headers.get('Content-Type').replace("image/","")
          file_name = ("%s.%s" % (file, format_file))
          Data.progress_status[title_value]["directory"] = download_path = os.path.join(os.getcwd(),location,file_name)
         
          
          loggon.info(f"<{title_value}> Connection Code: {resp.status_code}")
          response_code = resp.status_code
          if response_code < 300 and response_code >= 200:
            if response_code not in (200,206):
                loggon.warning(f"<{title_value}> Unexpected SUCCESSFUL HTTP response code: {response_code}")
          else:
            loggon.warning(f"<{title_value}> Unexpected http response code: {response_code}")
            continue 
        
          
            
          if not continued and not manual_fix:
            if os.path.isfile(download_path):
                current_size = os.path.getsize(download_path)
                file_size = int(resp.headers.get("content-length"))
                Data.progress_status[title_value]["Max"] = file_size
                Data.progress_status[title_value]["Bytes"] = current_size 
              
                if current_size == file_size:
                    return __complete_return()
                elif current_size > file_size:
                    Data.progress_status[title_value]["Bytes"] = 0
                    Data.progress_status[title_value]["Max"] = False
                    os.remove(download_path)
                    
                    continue
                else:
                  loggon.info(f"<{title_value}> Manual download resume")
                  Data_tsnap = file_size
                  Data_psnap = current_size
                  headers["Range"] = "bytes=%d-" % Data_psnap
                  manual_fix = True 
                  continue
                  
                    
        
          
          if not continued and not manual_fix:
            Data.progress_status[title_value]["Max"] = int(resp.headers.get('content-length'))
            Data_tsnap += int(resp.headers.get('content-length'))
        
        
          async with await anyio.open_file(download_path, "ab") as asf:
            async for chunk in resp.aiter_bytes(4096):
              
              Data_psnap += len(chunk)
              Data.progress_status[title_value]["Bytes"] = Data_psnap
              if not Data_psnap <= Data_tsnap:
                  loggon.exception(f"<{title_value}> File out of bounds resetting..")
                  __reset_progress()
                  continued = False
                  manual_fix = False
                  break
                  
                  
              await asf.write(chunk)
            else:
              return __complete_return()
            continue
          
          
      except httpx.HTTPError as e:
        timeout += 1
        if timeout < 7:
          loggon.exception(f"<{title_value}>Problem occured, retrying {timeout}/6")
          VolatileData.retry_proc.append(True)
          if manual_fix:
              Data.progress_status[title_value]["Bytes"] = 0
             
              if os.path.isfile(download_path):
                os.remove(download_path)
          await anyio.sleep(2)
          continue
        print(f"\nP:{title_value},Error: {e}, full data on logs")
        loggon.exception("DLException: ")
        return __incomplete_return()
  async with sem: 
    return await __start_process()
    
class Data_raw:
  def __init__(self):
    self.progress_status = {}
class VData:
  def __init__(self):
    self.response_proc = []
    self.retry_proc = [] 
  
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
Data = Data_raw()  
VolatileData = VData()

if __name__ == "__main__":
  Download(input(),1,"Downloads")
