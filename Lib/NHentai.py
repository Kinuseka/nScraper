from bs4 import BeautifulSoup
import re
import json
import urllib.request
import random
#I recommend reading into the source code of the nhentai website to get a better understanding of what my code really does

site_domain = "net"
headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}

def _build_url_opener():
  """Use stdlib 308 support when present (3.11+); otherwise backport it.

  Python 3.11 added HTTP 308 to urllib. Older versions raise HTTPError 308
  instead of following Location. 307 (3.3+) preserves the method like 308;
  302 is the fallback on very old urllib.
  """
  redirect = urllib.request.HTTPRedirectHandler
  if hasattr(redirect, "http_error_308"):
    return urllib.request.build_opener()
  remap_to = 307 if hasattr(redirect, "http_error_307") else 302
  class _HTTP308RedirectHandler(redirect):
    http_error_308 = redirect.http_error_302
    def redirect_request(self, req, fp, code, msg, headers, newurl):
      if code == 308:
        code = remap_to
      return redirect.redirect_request(self, req, fp, code, msg, headers, newurl)
  return urllib.request.build_opener(_HTTP308RedirectHandler)

_url_opener = _build_url_opener()
#Optional
def CheckLink(data, digit=False):
  '''For MODDERS:
  This part is where you modify your OWN link checker to your own target site to scrape.
  Most of the time there wont be any major edits other than the website you want to check.
  '''
  if digit:
    return(f"https://nhentai.{site_domain}/g/%s/" % data)
  if re.search(fr"https?://nhentai.{site_domain}/g/(\d+|/)", data.lower()):
    if not data.endswith("/"):
      data = data + "/"
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
    page = _url_opener.open(req)
    self.soup = BeautifulSoup(page, "html.parser")
    json_regex = r'JSON\.parse\("(.*?)"\)'
    # script = re.search(json_regex, (self.soup.find_all("script")[2].contents[0]).strip()).group(1).encode("utf-8").decode("unicode-escape")
    script = self.soup.find('script', {'data-url': re.compile(r'^/api/v2/galleries/')}) # We gather it directly from site to avoid rate limiting (I think)
    #IF THERE IS NO ERROR THEN PROCEED
    self.json = json.loads(json.loads(script.string).get('body', {}))
    # self.json = self.json[]

  def Pages(self):
    "Total available pages count"
    Page = len(self.json["pages"])
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
    data = self.json["pages"][value-1]
    file = data["path"].rsplit(".", 1)[-1]
    if file == "jpg":
      extension = "jpg"
    elif file == "png":
      extension = "png"
    elif file == "gif":
      extension = "gif"
    elif file == "webp":
      extension = "webp"
    else:
      print("WARNING AT PAGE: %s\nUNIDENTIFIED FORMAT '%s' DETECTED REPORT THIS BUG\nautoset: jpg" % (value, file))
      extension = "jpg"
    media_id = self.json["media_id"]
    cdns = self.fetch_cdn_urls()
    if cdns:
      rcdn_val = random.choice(cdns)
      cdn = rcdn_val
    else:
      cdn = "i3.nhentai.net"
    url = "https://%s/galleries/%s/%s.%s" % (cdn, media_id, value, extension)
    return url
  
  def fetch_cdn_urls(self):
    """Return list of CDN hosts from window._n_app.image_cdn_urls if available."""
    try:
      scripts = self.soup.find_all("script")
      for s in scripts:
        # Safely get the script content as text
        content = None
        if s.string:
          content = s.string
        elif s.contents:
          try:
            content = "".join(str(x) for x in s.contents)
          except Exception:
            content = None
        if not content or "image_cdn_urls" not in content:
          continue
        match = re.search(r'image_cdn_urls\s*:\s*(\[[^\]]*\])', content)
        if match:
          array_text = match.group(1)
          try:
            return json.loads(array_text)
          except Exception:
            # Attempt a simple cleanup for minor syntax differences
            cleaned = re.sub(r",\s*]", "]", array_text)
            cleaned = cleaned.replace("'", '"')
            try:
              return json.loads(cleaned)
            except Exception:
              return []
      return []
    except Exception:
      return []
   
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
    