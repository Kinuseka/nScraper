import Lib
from functools import wraps
import requests
import sys
import os
import time
import re
def Data_parse(data):
  """For MODDERS:
  1.If you want to add a Link verifier to prevent invalid link error then you have nothing to edit here, however you can delete this to disable this feature.
  2.You can modify the 1st condition if the target site does not support or does not use numbers to identify their gallery.
  3.If you want to use links, be sure that the user has to include http:// or https:// to prevent further problems.
  """
  if data.isdigit():
    data = Lib.CheckLink(data, opt=True)
    return(0,data)
  elif "http://" in data or "https://" in data:
    result,data = Lib.CheckLink(data)
    return(result,data)
  else:
    return(1,"A link should have http:// or https://")
def validatename(func):
  @wraps(func)
  def wrapper(self):
    word = func(self)
    word = word.replace("\\","_")
    word = word.replace("/","_")
    return word
  return wrapper

def sorttags(func):
  """:
    Use this Wrapper to sort your tags
    into a list.
    """
  @wraps(func)
  def wrapper(self):
    tags = func(self)
    return tags
  return wrapper

current = {"File1":{"speed":0,"status":False},"File2":{"speed":0,"status":False},"File3":{"speed":0,"status":False},"File4":{"speed":0,"status":False},"File5":{"speed":0,"status":False}}
results = []
class CommunicateApi:
  """Info:
  Used for the __main__ to communicate with the NHentai.py.
  theres not alot you can do to modify this
  """
  def __init__(self, data):
      self.Handler = Lib.Api(data)
  def Pages(self):
    data = self.Handler.Pages()
    return(data)
  @sorttags #Wrapper that will sort tags
  def Tags(self):
    "I recommend to keep your tag sorting algorithm readable"
    data = self.Handler.Tags()
    return(data)
  @validatename #Wrapper that modify an invalid name
  def Title(self):
    data = self.Handler.Title()
    return(data)
  def Link_Page(self,var):
    """Info:
    The variable 'var' has to accept integer value that points to the certain page 
    example: var = 10 will return a direct link to page 10. Refer to the Lib/NHentai.py what link to return
    """
    data_list = []
    for num in range(1,(int(var)+1)):
      data = self.Handler.Direct_link(num)
      data_list.append(data)
    return(data_list)

  def Download(self,link,title_value,location,assigned):
    """Info:
    Theres not alot to edit here except for the arguments
    """
    start = time.process_time()
    try:
      current["File%s" % assigned]["status"] = True
      #current["File%s" % assigned] = 0
      response = requests.get(link,stream=True)
      format_file = response.headers.get('Content-Type')
      format_file = format_file.replace("image/","")
      #Downloader
      file_name = title_value
      file_name = ("%s.%s" % (file_name, format_file))
      with open(os.path.join(os.getcwd(),location,file_name), "wb") as f:
        current["File%s" % assigned]["status"] = True
        total_length = response.headers.get('content-length')
        if total_length is None: # no content length header
          f.write(response.content)
        else:
          total_length = int(total_length)
          label = ("mb" if (float(total_length / 1000) >= 1000) else "kb")
          size = (round(total_length/1000000,2) if (label=="mb") else (round(total_length/1000,2)))
            #print("\rDownloading %s (%s%s)" % (file_name,size,label))
          dl = 0
          for data in response.iter_content(chunk_size=8192):
            dl += len(data)
            f.write(data)
            done = int(50 * dl / total_length)
            bytespeed = (dl/int(time.process_time() - start))
            current["File%s" % assigned]["speed"] = bytespeed // 1000
           #sys.stdout.write("\r[%s%s]%s%s" % ('=' * done, ' ' * (50-done),done*2,"%")) 
           #sys.stdout.flush()
    #print("\n")
    except requests.exceptions.ConnectionError:
      pass
    results.append(file_name)
    current["File%s" % assigned]["status"] = False
    #current["File%s" % assigned]["speed"] = 0


if __name__ == "__main__":
  Download(input(),1,"Downloads")