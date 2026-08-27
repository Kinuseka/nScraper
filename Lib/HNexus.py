from bs4 import BeautifulSoup
import re
import json
import urllib.request
import base64

site_domain = "com"
headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}

def CheckLink(data, digit=False):
  '''For MODDERS:
  This part is where you modify your OWN link checker to your own target site to scrape.
  Most of the time there wont be any major edits other than the website you want to check.
  '''
  if digit:
    return(data)
  match = re.search(
        fr"https?://hentainexus\.{site_domain}/(?:read|view)/(\d+)/?$",
        data
    )
  if match:
    return(0, match.group(1))
  else:
    return(2, "Link is not HentaiNexus")
  
 
class Api:
    
    def __init__(self,data):
        '''
        argument 'data' should be a valid link the target booklet
        '''
        self.name = "HentaiNexus" #Directory label
        #HNexus has an encrypted data found /read/ we can speed up load times by decoding that instead and get the links directly.
        self.hostname = "hentainexus.com"
        self.view_link = f"https://{self.hostname}/view/{data}"
        self.read_link = f"https://{self.hostname}/read/{data}"
        match = re.search(fr"https?://hentainexus.{site_domain}/(?:read|view)/(\d+)/?$", self.read_link) or re.search(fr"https?://hentainexus.{site_domain}/(?:read|view)/(\d+)/?$", self.view_link)
        if match:
            self.gallery_id = match.group(1)
        else:
            raise ValueError("Invalid link")
        # Get the view page
        req = urllib.request.Request(self.view_link, headers=headers)
        page = urllib.request.urlopen(req)
        self.soup_view = BeautifulSoup(page, "html.parser")
        # Get the read page
        req = urllib.request.Request(self.read_link, headers=headers)
        page = urllib.request.urlopen(req)
        self.soup_read = BeautifulSoup(page, "html.parser")
        scripts = self.soup_read.find_all("script")
        data_regex = r'initReader\(\s*["\']([^"\']+)["\']'
        pattern = re.compile(data_regex, re.DOTALL)
        captured_final = ""
        for each in scripts:
            if not each.contents:
                continue
            captured = each.contents[0]
            if "initReader" in captured:
               captured_final = captured.strip()    
               break 
        else:
            print("CANNOT EXTRACT DATA FROM SITE, REPORT THIS BUG")
            raise LookupError("Cannot find data from the site")

        match = pattern.search(captured_final)
        obf_data = match.group(1).strip()
        byte_data = base64.b64decode(obf_data)
        #Decode data
        h = bytearray(byte_data[:64])
        dH64 = self._xor_decipher(h)
        p16 = self._16p()
        sel = self._find_selector(dH64)
        step_p = p16[sel]
        S = self._ksa(dH64)
        tail = byte_data[64:]
        #Parse data
        text = self._prga(S, step_p, tail)
        self.json = json.loads(text)


    def _xor_decipher(self, h64: bytearray):
        hbytes = self.hostname.encode('latin1')
        dH64 = h64  
        for i in range(min(len(hbytes), 64)):
            dH64[i] ^= hbytes[i]
        return dH64
    
    def _16p(self):
        prm, n = [], 2
        while len(prm) < 16:
            for p in prm:
                if n % p == 0:
                    break
            else:
                prm.append(n)
            n += 1
        return prm

    def _find_selector(self, h64: bytes) -> int:
        v = 0
        for b in h64:
            v ^= b
            for _ in range(8):
                v = ((v >> 1) ^ 0x0C) if (v & 1) else (v >> 1)
        return v & 0x07

    def _ksa(self, h64: bytes):
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + h64[i % 64]) & 0xFF
            S[i], S[j] = S[j], S[i]
        return S
    
    def _prga(self, S, step_p: int, tbytes: bytes) -> bytes:
        i = j = e = t = 0
        out = bytearray(len(tbytes))
        for a in range(len(tbytes)):
            i = (i + step_p) & 0xFF
            j = (e + S[(j + S[i]) & 0xFF]) & 0xFF
            e = (e + i + S[i]) & 0xFF
            S[i], S[j] = S[j], S[i]
            t = S[(j + S[(i + S[(t + e) & 0xFF]) & 0xFF]) & 0xFF]
            out[a] = tbytes[a] ^ t
        return bytes(out)
    
    def Pages(self):
        "Total available pages count"
        return len(self.json)
        
    def Tags(self):
        """Should return target link tags IF available.
        """
        metadata = {}
        table = self.soup_view.find("table", class_="view-page-details")
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) != 2:
                    continue  # skip malformed rows
                key = cols[0].get_text(strip=True)
                value_td = cols[1]
                # Handle nested tags like links or spans gracefully
                # Extract clean text, but preserve list for multiple tags
                if key.lower() == "tags":
                    tags = [a.get_text(strip=True).split(" (")[0] for a in value_td.find_all("a")]
                    metadata[key] = tags
                else:
                    metadata[key] = value_td.get_text(" ", strip=True)
        return metadata
    def Title(self):
        "Booklet complete title"
        return self.soup_view.find("h1", class_="title").get_text(strip=True)
    
    def Direct_link(self,value):
        """For MODDERS:
        This function is used to RETURN a valid direct link to the targeted image.
        The image must be a downloadable ready to be downloaded link
        'value' should point to the exact page of the link
        e.g. value = 20, Return https://example.site/page20.jpg
        """
        data = self.json[value-1]
        image = data.get('image') or data.get('image_avif') or data.get('image_fallback')
        
        return image

class Iterdata:
    """[Optional Feature]
    File Iterator used to automatically detect links in a text file IF provided
    """
    def __init__(self,file_directory):
        self.available = True #Used to indicate that the feature is available. False if None
        self.data = file_directory
        self._index = -1
        self.temptxt = []
    
    def extract_numbers(self, text):
        pattern = rf"(?<!#)(?<!\S)(?:https?:\/\/hentainexus\.{site_domain}\/(?:read|view)\/)?(\d{{1,6}})(?=(?:[,\s]|$))"
        matches = re.findall(pattern, text)
        links_and_numbers = []
        for match in matches:
            print(match)
            if match:
                links_and_numbers.append(match)
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
        raise StopIteration
        
    def __reversed__(self):
        return self.temptxt[::-1]
    
    def __exit__(self,tp,v,tb):
        #Close an open directory
        self.txt_line.close()