__version__ = '0.9.0'

import contextlib
import time, os,datetime, sys, re


NM2KM=1.852
HOUR2SEC=3600.
DAYS2SEC=HOUR2SEC*24.

UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$')


@contextlib.contextmanager
def stopwatch(message, context):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        #sys.stderr.write('Total elapsed time for %s at %s : %.3f' % (message,context, t1 - t0))
        print('Total elapsed time for %s at %s : %.3f' % (message,context, t1 - t0), file=sys.stderr, flush=True)
        
        
def logme(messg):
    print(messg, file=sys.stderr, flush=True)
    

def ensureProtocol(urlstr):
    if urlstr.find('://') < 2:
        return f"http://{urlstr}"
    return urlstr
    
def ensureURLPath(url, pathstr):
    url = ensureProtocol(url)
    if not pathstr or len(pathstr) <1:
        return url
    
    if url[-1] != '/':
        if pathstr[0] == '/':
            return  url+pathstr
        return url+'/'+ pathstr
    elif pathstr[0] == '/':
            return  url+pathstr[1:]
        
    return url+ pathstr





def uuid():
    from uuid_extensions import uuid7str
    return uuid7str()

    
def isValidUUID(str_uuid):
    # VERSION AGNOSTIC
    return  bool(str_uuid and UUID_PATTERN.match(str_uuid.lower()))


def isValidString(strval):
    if not strval:
        return False
    
    return len(str(strval).strip()) > 0;

def inferParse(targettype,value):
    
    
    if targettype == int:
        return float(int(value))
    
    if targettype == float:
        return float(value)
    
    
    if targettype == datetime.date:
        return datetime.datetime.fromisoformat(str(value)).date()

    if targettype == datetime.datetime:
        return datetime.datetime.fromisoformat(str(value)) 
    
    return str(value)

def mergeJson(dict0, dict1):
    
    if not isinstance(dict1,dict):
        return True
    
    for k in dict1:
        if k in dict0:
            if mergeJson(dict0[k],dict1[k]):
                dict0[k]= dict1[k]
        else:
            dict0[k]= dict1[k]
            
    return False
    