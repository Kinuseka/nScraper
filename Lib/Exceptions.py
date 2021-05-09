#Create Custom Exceptions here

class SearchNotFound(Exception):
  """A custom exception when no results are found.
  You may call this exception when 404 search not found is returned
  """
  def __init__(self,message):
    self.message = message
    super().__init__(self.message)

  def __str__(self):
    """You may modify error message shown at the traceback by editing the string below
    self.message is the message of the raised error
    """
    return(f'{self.message}')