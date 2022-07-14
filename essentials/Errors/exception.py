
class NotFound(Exception):
     def __init__(self, *args, **kwargs):
        default_message = 'Not Found'
        self.code = 404

        # if any arguments are passed...
        # If you inherit from the exception that takes message as a keyword
        # maybe you will need to check kwargs here
        if args:
            # ... pass them to the super constructor
            super().__init__(*args, **kwargs)
        else: # else, the exception was raised without arguments ...
                 # ... pass the default message to the super constructor
            super().__init__(default_message, **kwargs)

class NetworkError(Exception):
    def __init__(self,code,content,*args,**kwargs):
        default_message = 'There has been a connection error'
        self.code = code
        self.content = content

        if args:
            # ... pass them to the super constructor
            super().__init__(*args, **kwargs)
        else: # else, the exception was raised without arguments ...
                 # ... pass the default message to the super constructor
            super().__init__(default_message, **kwargs)

class HTTPError(Exception):
    def __init__(self,code,content,*args,**kwargs):
        default_message = 'There has been an HTTP error'
        self.code = code
        self.content = content

        if args:
            # ... pass them to the super constructor
            super().__init__(*args, **kwargs)
        else: # else, the exception was raised without arguments ...
                 # ... pass the default message to the super constructor
            super().__init__(default_message, **kwargs)

class CloudflareBlocked(Exception):
    def __init__(self,code,content,*args,**kwargs):
        default_message = 'CF has persistently blocked us, please report this issue.'
        self.code = code
        self.content = content

        if args:
            # ... pass them to the super constructor
            super().__init__(*args, **kwargs)
        else: # else, the exception was raised without arguments ...
                 # ... pass the default message to the super constructor
            super().__init__(default_message, **kwargs)

