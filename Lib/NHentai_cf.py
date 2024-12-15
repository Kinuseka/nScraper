import CFSession
from logging import exception
from bs4 import BeautifulSoup
import re
import json
import pickle
import os
from . import NHentai
from essentials.Errors import exception as cferror
#I recommend reading into the source code of the nhentai website to get a better understanding of what my code really does

site_domain = "net"
headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}

#Main API
class Api:
  # Use INIT to initialize the needed data, for increased and faster loading times to other functions
  def __init__(self,data):
    '''
    argument 'data' should be a valid link the target booklet
    '''
    
    self.name = "NHentai" #Directory label
    #NHENTAI SITE FORTUNATELY HAS A DEDICATED JSON EMBEDDED INTO A SCRIPT FILE THAT YOU CAN USE TO GAIN INFORMATION FROM THE SITE. 
    #DIFFERENT SITES MIGHT NOT HAVE A JSON FILE SO YOU WILL HAVE TO DO THE PROCESS MANUALLY

    caught_exception = None
    try:
      session = CFSession.cfSession(headless_mode=True)
      content = session.get(data)
      content.raise_for_status()
    except (CFSession.cfexception.HTTPError, CFSession.cfexception.NotFound ) as e:
      http_code = e.response.status_code
      caught_exception = e
      if http_code == 404:
        raise cferror.NotFound()
      else:
        raise cferror.HTTPError
    except CFSession.cfexception.CFException as e:
      caught_exception = e
      caught_message = "There has been issues with trying to connect"
      raise cferror.NetworkError()
    page = content.content
    self.soup = BeautifulSoup(page, "html.parser")
    json_regex = r'JSON\.parse\("(.*?)"\)'
    script = re.search(json_regex, (self.soup.find_all("script")[2].contents[0]).strip()).group(1).encode("utf-8").decode("unicode-escape")
    #IF THERE IS NO ERROR THEN PROCEED
    self.json = json.loads(script)


    self.__preloader_pages()

  def Pages(self):
    "Total available pages count" 
    Page = len(self.json["images"]["pages"])
    return Page

  def Tags(self):
    """For MODDERS:

    For better readability for humans or other programs, I recommend you use Json to serialize your data.
    """
    Tag = self.json["tags"]
    return Tag

  def Title(self):
    title = self.json["title"]["english"]
    return title



  def Direct_link(self,value): 
    """For MODDERS:
    This function is only used to RETURN a valid direct link to the targeted image.
    The variable 'value' is the episode/page of the certain image to return. 
    """
    data = self.preloaded_data[value-1]
    file = data["t"]
    if file == "j":
      extension = "jpg"
    elif file == "p":
      extension = "png"
    elif file == "g":
      extension = "gif"
    elif file == "w":
      extension = "webp"
    else:
      print("WARNING AT PAGE: %s\nUNIDENTIFIED FORMAT DETECTED REPORT THIS BUG\nautoset: jpg" % value)
      extension = "jpg"
    media_id = self.json["media_id"]
    url = "https://i3.nhentai.net/galleries/%s/%s.%s" % (media_id, value, extension)
    return url

  def __preloader_pages(self):
    dict_data = self.json["images"]["pages"]
    data = []
    try:
      for v in range(self.Pages()):
         data.append(dict_data[f"{v+2}"])
    except TypeError as e:
      data = dict_data
    self.preloaded_data = data
   
Iterdata = NHentai.Iterdata
CheckLink = NHentai.CheckLink