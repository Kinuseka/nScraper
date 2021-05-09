import requests
import re
from bs4 import BeautifulSoup
import json
from . import Exceptions
#I recommend reading into the source code of the nhentai website to get a better understanding of what my code really does


headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}
#Optional
def CheckLink(data, **opt):
  '''For MODDERS:
  This part is where you modify your OWN link checker to your own target site to scrape.
  Most of the time there wont be any major edits other than the website you want to check.
  '''
  if opt:
    return("https://nhentai.net/g/%s" % data)
  if re.search("https?://nhentai.net/g/(\d+|/)", data.lower()):
    return(0, data)
  else:
    return(2, "Link is not nHentai")

#Main API
class Api:
  # Use INIT to initialize the needed data, for increased and faster loading times to other functions
  def __init__(self,data):
    '''
    argument 'data' should be a valid gallery/link to a certain doujin. 
    '''
    r = requests.get(data, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    try:
      script = (soup.find_all("script")[2].contents[0]).strip().replace("window._gallery = JSON.parse(", "").replace(");","")
    except IndexError:
      #ONLY OCCURS WHEN THERE IS NO RESULTS
      error = {"error_message":"","e":""}
      try:
        error_scrape = soup.find("div",class_="container error")
        status = error_scrape.find("h1").text.strip()
        status_message = error_scrape.find("p").text.strip()
        error["error_message"] = ("%s %s" % (status,status_message))
      except AttributeError as e:
        #Precautionary Catcher. rarely occurs
        error["e"] = e
      raise_message = ("%s %s" % (error["error_message"], error["e"]))
      raise Exceptions.SearchNotFound(raise_message)
    #IF THERE IS NO ERROR THEN PROCEED
    self.json = json.loads(json.loads(script))

  def Pages(self):
    Page = len(self.json["images"]["pages"])
    return(Page)

  def Tags(self):
    """For MODDERS:
    For better readability for humans or other programs, I recommend you use Json to serialize your data.
    """
    TagList = []
    Tag = self.json["tags"]
    for num,data in enumerate(Tag):
      TagList.append(data)
    return(Tag)

  def Title(self):
    title = self.json["title"]["english"]
    return(title)


  def Direct_link(self,value): 
    """For MODDERS:
    This function is only used to RETURN a valid direct link to the targeted image.
    The variable 'value' is the episode/page of the certain image to return. 
    """
    data = self.json["images"]["pages"][value-1]
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
    return(url)