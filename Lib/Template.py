from bs4 import BeautifulSoup
import re
import json
import urllib

headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"}

def CheckLink(data, digit=False):
  '''For MODDERS:
  This part is where you modify your OWN link checker to your own target site to scrape.
  Most of the time there wont be any major edits other than the website you want to check.
  '''
  pass
  
 
class Api:
    
    def __init__(self,data):
        '''
        argument 'data' should be a valid link the target booklet
        '''
        self.name = "APINAME" #Directory label
        
        pass
    
    def Pages(self):
        "Total available pages count"
        pass
        
    def Tags(self):
        """Should return target link tags IF available.
        """
        pass
   
    def Title(self):
        "Booklet complete title"
        pass
    
    def Direct_link(self,value):
        """For MODDERS:
        This function is used to RETURN a valid direct link to the targeted image.
        The image must be a downloadable ready to be downloaded link
        'value' should point to the exact page of the link
        e.g. value = 20, Return https://example.site/page20.jpg
        """
    
    
class Iterdata:
  """[Optional Feature]
  File Iterator used to automatically detect links in a text file IF provided
  """
    def __init__(self,file_directory):
        self.available = False #Used to indicate that the feature is available. False if None
        self.data = file_directory
        
    def __iter__(self):
        return self
        
    def __enter__(self):
        return self
    
    def __next__(self):
        raise StopIteration
        
    def __reversed__(self):
        return None
    
    def __exit__(self,**args):
        #Close a open directort
        pass
    
    
    
        