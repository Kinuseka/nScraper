from bs4 import BeautifulSoup
import re
import json
import yaml
import urllib.request
from . import NHentai
#I recommend reading into the source code of the nhentai website to get a better understanding of what my code really does

site_domain = "to"
headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}

#Main API
class Api:
  # Use INIT to initialize the needed data, for increased and faster loading times to other functions
  def __init__(self,data):
    '''
    argument 'data' should be a valid link the target booklet
    '''
    
    self.name = "NHentai_mirror" #Directory label
    #NHENTAI SITE FORTUNATELY HAS A DEDICATED JSON EMBEDDED INTO A SCRIPT FILE THAT YOU CAN USE TO GAIN INFORMATION FROM THE SITE. 
    #DIFFERENT SITES MIGHT NOT HAVE A JSON FILE SO YOU WILL HAVE TO DO THE PROCESS MANUALLY
    req = urllib.request.Request(data, headers=headers)
    page = urllib.request.urlopen(req)
    self.soup = BeautifulSoup(page, "html.parser")
    script_p1 = (self.soup.find_all("script"))
    for num, script_line in enumerate(script_p1):
      try:
        script_line = script_line.contents[0].strip()
        script_p2 = re.search(r'N.gallery\((.*?)gallery.init\(', script_line, re.DOTALL)
        if script_p2:
          break
        
      except IndexError as e:
        pass
      except AttributeError as e:
        pass

    script_p2 = re.sub(r'(^N.gallery\()|(gallery.init\($)', '', script_p2.group()).replace(");","")
    tscript = str(script_p2)
    #IF THERE IS NO ERROR THEN PROCEED
    
    script = yaml.safe_load(tscript)
  
    self.json = script

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
    else:
      print("WARNING AT PAGE: %s\nUNIDENTIFIED FORMAT DETECTED REPORT THIS BUG\nautoset: jpg" % value)
      extension = "jpg"
    media_id = self.json["media_id"]
    url = "https://i.nhentai.net/galleries/%s/%s.%s" % (media_id, value, extension)
    #url = "https://t.dogehls.xyz/galleries/%s/%s.%s" % (media_id, value, extension)
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
   
def CheckLink(data, digit=False):
  '''For MODDERS:
  This part is where you modify your OWN link checker to your own target site to scrape.
  Most of the time there wont be any major edits other than the website you want to check.
  '''
  if digit:
    return(f"https://nhentai.{site_domain}/g/%s" % data)
  if re.search(f"https?://nhentai.{site_domain}/g/(\d+|/)", data.lower()):
    return(0, data)
  else:
    return(2, "Link is not nHentai")
Iterdata = NHentai.Iterdata
    