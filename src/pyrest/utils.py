
import json, os, datetime
from pyrest import stopwatch

def loadJsonAndResolve(f):
    '''
    load the json file and resolve ENV VARS
    NOTE: if the variable is not set in will be replaced by an empty string
    '''
    with open(f,'r') as fp:
        ddlines = fp.read()
        return json.loads(os.path.expandvars(ddlines))
    
    


def mergeJsonFromFiles(jsonfs):
    
    jsondicts = []
    for f in jsonfs:
        jsondicts.append(loadJsonAndResolve(f.strip(" ").strip('\t').strip("\n").strip(" ")))
        #with open(f,'r') as fp:
        #    jsondicts.append(json.load(fp))
    return mergeJsonDicts(jsondicts)


 
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

def mergeJsonDicts(jsondicts):        
    primdict = jsondicts[0]
    for i in range(1,len(jsondicts)):
        mergeJson(primdict,jsondicts[i])
    return primdict
    
    
def mergeJsonFiles(fpaths):
    import tempfile
    
    jsonfs = fpaths.split(",")
    if len(jsonfs) == 1:
        return fpaths
    
    primdict = mergeJsonFromFiles(jsonfs)
    fd = tempfile.NamedTemporaryFile(prefix="config_merged",mode='w',delete=False)
    json.dump(primdict,fd, indent=2)
    return fd.name
        
        

        
from threading import Thread
class ObservableThread(Thread):
    
    def __init__(self,pid, func, args,kwargs):
        Thread.__init__(self, name=pid)
        self._buf = []
        self._func= func 
        self.kwargs = kwargs
        self.args = args
        self._startDT = None
        self._lastMod = None
        self._reconstituted = False
        self._ended = False
        self._results = None
        
    def write(self,bstr):
        if bstr:
            if hasattr(bstr,"decode"):
                # we have a bytes
                bstr = bstr.decode()
                
            bstr = bstr.replace('\n','')
            if len(bstr) < 1:
                return
            self._buf.append(bstr)
            self._lastMod = datetime.datetime.now()
            
    
    def flush(self):
        pass
    
    def close(self):
        pass
    
    @property
    def closed(self):
        return self._reconstituted or not self.is_alive()
        
        
    def lastTouched(self):
        return self._lastMod
    
    def run(self):
        from stdio_proxy import redirect_stdout
        with stopwatch("Running Observable",self._name):
            self._startDT = datetime.datetime.now()
            try:
                with redirect_stdout(self):
                    self._results = self._func(*self.args, **self.kwargs)
                #logme(f" run setting ended")
                self._ended = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.write(f"Error {e}")
                
                
    def status(self):
        if self._buf:
            return self._buf[-1] , self._lastMod ,not self.closed
        
        return "", None, not self.closed
    
    def messages(self):
        if self._buf:
            return self._buf, self._lastMod, not self.closed
        
        return "", None, not self.closed
     
    def endedNormaly(self):
        return self._ended 
        
    def result(self):
        return self._results    
    
    ## custom pickling
    def __setstate__(self, d):
        self._buf = d["messages"]
        self._startDT = d["start"]
        self._lastMod = d["last"]
        #logme(f" set-state setting ended")
        if "ended" in d:
            self._ended = d["ended"]
        
        self._reconstituted = True
        if "result" in d:
            self._results = d["result"]
            
    def __getstate__(self):
        #logme(f" get-state setting ended")
        state = {"messages":self._buf,
                "start":self._startDT,
                "last":self._lastMod,
                "result":self._results }
        
        if hasattr(self,"_ended"):
            state["ended"] = self._ended
        return state
        

        
        

from threading import Timer

class RepeatTimer(object):
    def __init__(self, interval, function, defer = 0.):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.is_running = False
        
        if defer > 0.:
            t = Timer(defer, self.start)
            t.start()
        else:
            self.start()
        
        

    def _run(self):
        self.is_running = False
        # start the next round
        self.start()
        # execute the delegate
        self.function()

    def start(self):
        if not self.is_running: 
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
    
    
        