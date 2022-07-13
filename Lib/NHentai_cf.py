from logging import exception
from bs4 import BeautifulSoup
import re
import json
import yaml
import requests
import pickle

#I recommend reading into the source code of the nhentai website to get a better understanding of what my code really does

site_domain = "net"
headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}
#Optional
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

    #Initialize path
    self.cookie_path = HSite.cookie_path
    self.session_path = HSite.session_path
    self._data_level = data
    #Check token
    self.__reload_cf_token()
    
    #Load Cookies
    s = requests.Session()
    self.__set_cookies(s)
    

    caught_exception = None
    for t in range(0,2):
      try:
        content = s.get(data)
        content.raise_for_status()
        break
      except requests.exceptions.HTTPError as e:
        http_code = e.response.status_code
        caught_exception = e
        if http_code == 404:
          raise cferror.NotFound()
        elif http_code == 503:
          #CF blocked us, update the token
          #Recheck token
          self.__reload_cf_token(reset=True)
          self.__set_cookies(s)
      except requests.exceptions.ConnectionError as e:
        caught_exception = e
        caught_message = "There has been issues with trying to connect"
        raise cferror.NetworkError()

    else:
      caught_code = caught_exception.response.status_code
      caught_content = caught_exception.response.content
      caught_message = "There has been issues communicating with the server"
      if caught_code == 503:
        raise cferror.CloudflareBlocked(caught_code,caught_content)
      raise cferror.HTTPError(caught_code,caught_content,caught_message)



    page = content.content
    self.soup = BeautifulSoup(page, "html.parser")
    script = (self.soup.find_all("script")[2].contents[0]).strip().replace("window._gallery = JSON.parse(", "").replace(");","")
    #IF THERE IS NO ERROR THEN PROCEED
    self.json = json.loads(json.loads(script))


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

  def __reload_cf_token(self,reset=False):
    cookieStatus =  HSite.SiteCFBypass.cookie_available()
    if not cookieStatus[0] or reset:
      NHS = HSite.SiteCFBypass(self._data_level)
      if reset:
        HSite.SiteCFBypass.delete_cookies()
      NHS.start()
      NHS.join()

  def __set_cookies(self, session):
    cookies = pickle.load(open(self.cookie_path,"rb"))
    selenium_headers = pickle.load(open(self.session_path,"rb"))
    session.headers.update({"user-agent": selenium_headers})
    for cookie in cookies:
      session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
   
class Iterdata:
  """File Iterator used to automatically detect links inside a text file
  """
  def __init__(self,data):
    self.available = True #Used to indicate that the feature is available. False if none
    self.data = data
    self._index = -1
    self.temptxt = []
  def __iter__(self):
    return self
  def __enter__(self):
    self.txt_line = open(self.data,"r")
    for rawline in self.txt_line:
      for tline in rawline.replace(","," ").split():
        if not tline.isdigit():
          continue
        if len(tline) > 6:
          long_line = re.findall('.{1,6}', tline)
          for fixline in long_line:
            self.temptxt.append(fixline)
        self.temptxt.append(tline)
    return self
  def __next__(self):
    self._index += 1 
    if self._index >= len(self.temptxt):
      raise StopIteration
    return self.temptxt[self._index] 
  def __reversed__(self):
    return self.temptxt[::-1]
  def __exit__(self,tp,v,tb):
    self.txt_line.close()
    

if __name__ == "__main__":
  from ..essentials import HSite
  from ..essentials.Errors import exception as cferror
else:
  from essentials import HSite
  from essentials.Errors import exception as cferror