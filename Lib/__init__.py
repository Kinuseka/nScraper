import importlib

_module_name = "NHentai"

_classes = ("Api","Iterdata","CheckLink")
_package_name = "Lib"
_full_module = "%s.%s" % (_package_name,_module_name)


Api = getattr(importlib.import_module(_full_module),_classes[0])
Iterdata = getattr(importlib.import_module(_full_module),_classes[1])
CheckLink = getattr(importlib.import_module(_full_module),_classes[2])


#FOR MODDERS:
#YOU CAN CHANGE THE THE API EXAMPLE:
###NHentai ----> Anyname (The API you created)
####IF YOU EVER CHANGE THE NAME YOU ONLY NEED TO CHANGE THE NAME OF THE FILE ON THE __init__ only so you do not have to modify the main code.