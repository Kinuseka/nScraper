from bs4 import BeautifulSoup
import re
import json
import urllib.request
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
    req = urllib.request.Request(data, headers=headers)
    page = urllib.request.urlopen(req)
    self.soup = BeautifulSoup(page, "html.parser")
    json_regex = r'JSON\.parse\("(.*?)"\)'
    script = re.search(json_regex, (self.soup.find_all("script")[2].contents[0]).strip()).group(1).encode("utf-8").decode("unicode-escape")
    #IF THERE IS NO ERROR THEN PROCEED
    self.json = json.loads(script)

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
    data = self.json["images"]["pages"][value-1]
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
      print("WARNING AT PAGE: %s\nUNIDENTIFIED FORMAT '%s' DETECTED REPORT THIS BUG\nautoset: jpg" % (value, file))
      extension = "jpg"
    media_id = self.json["media_id"]
    url = "https://i3.nhentai.net/galleries/%s/%s.%s" % (media_id, value, extension)
    return url
   
class Iterdata:
  """File Iterator used to automatically detect links inside a text file
  """
  def __init__(self,data):
    self.available = True #Used to indicate that the feature is available. False if none
    self.data = data
    self._index = -1
    self.temptxt = []
  
  def extract_numbers(self, text):
    pattern = r'(http[s]?://nhentai\.net/g/(\d{1,6})|(?<!#)(?<!\S)\b\d{1,6}(?:[,]\d{1,6})?\b(?!\S))'
    matches = re.findall(pattern, text)

    links_and_numbers = []
    for match in matches:
        if match[0].startswith("http") or match[0].startswith("https"):
            links_and_numbers.append(match[0])
        else:
            links_and_numbers.append(match[0])
    return links_and_numbers
  def __iter__(self):
    return self
  def __enter__(self):
    self.txt_line = open(self.data,"r")
    full_txt = self.txt_line.read()
    extracted = self.extract_numbers(full_txt)
    self.temptxt = extracted  
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
    