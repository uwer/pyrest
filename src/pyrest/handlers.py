



import datetime, sys, os, pathlib, time
from pyrest.utils import ObservableThread, mergeJsonFiles,RepeatTimer
from pyrest import uuid, stopwatch
from classy_fastapi import ( Routable, 
                             get,delete,
                             put, post
                             )

from fastapi import Request,UploadFile,File,Path


from typing import Any

class MessageStore():
    '''
    Handler to maintain log messages on async calls,
    and to provide a callback mechanism for the state of these async executions 
    
    
    '''
    __instance = None
    
    
    @staticmethod
    def getInstance(store_loader = None):
        
        if MessageStore.__instance is None:
            MessageStore.__instance = MessageStore(store_loader)
            
        return MessageStore.__instance
    
    
    def __init__(self, store_loader = None):
        '''
        store_loader is a facility that provides a mechanism to store/pickle and reload the state of the registry
        it must provide a callable that takes 2 arguments - 
        - action (set, get)
        - the objec t to store or none
        '''
        self._registry = {}
        
        
        self._store_loader = store_loader
        
        if not store_loader is None:
            if hasattr(store_loader, "get"):
                self._registry = store_loader.get("message-store")
            elif callable(store_loader):
                self._registry = store_loader("get","message-store")
                
                
        self._cleanupTimer = RepeatTimer(3600, self.__cleanup,86400)
        # for testing 30 sec
        self._storeTimer = RepeatTimer(30, self.__store,10)
        
        self._storring = False
        self._cleaning = False
        
        from pyrest._prom import hasProm
        if hasProm():
            from pyrest._prom import createGauge
            self._pgauge_ntasks = createGauge("messagestore-ntasks","MessageStore Ntasks")
            self._pgauge_ntasks.callback(self._gauge_ntasks)
            self._pgauge_nrunning = createGauge("messagestore-nrunning","MessageStore NRunning")
            self._pgauge_nrunning.callback(self._gauge_nrunning)
        
    def __cleanup(self):
        triggerdate = datetime.datetime.now() - datetime.timedelta(days=2)
        self._cleanupBefore(triggerdate)
        
    def _cleanupBefore(self,triggerdate):
    
        if self._cleaning:
            return False 
        
        self._cleaning = True
        todelete = []
        for k in self._registry:
            obj = self._registry[k]
            if obj.closed and not obj.lastTouched() is None and obj.lastTouched() < triggerdate:
                #del self._registry[k]
                todelete.append(k)
            
        for k in  todelete:
            del self._registry[k]
        
        
        
        self.__store()
        self._cleaning = False
        return True


    def __store(self):
        
        if  self._store_loader is None:
            return

                
        if self._storring:
            return
        try:
            self._storring = True
            if hasattr(self._store_loader, "get"):
                self._store_loader.set("message-store",self._registry)
            elif callable(self._store_loader):
                self._store_loader("set","message-store",self._registry)

        except Exception as e:
            print(e)
            
        finally:
            self._storring = False
    
    def _gauge_ntasks(self):
        return len(self._registry)
    
    def _gauge_nrunning(self):
        running = 0
        self._cleaning = True
        try:
            for k in self._registry:
                if not self._registry[k].closed:
                    running+=1
        finally:
            self._cleaning = False
        return running
    
    def addProcess(self, func, args = [], kwargs = {}):
        
        pid = uuid()
        obj = ObservableThread(pid,func, args,kwargs)
        self._registry[pid] = obj
        return pid, obj
    
    def processEndedNormaly(self, pid):
        if self.has(pid):
            return self._registry[pid].endedNormaly()
        return None
    
    def processResults(self, pid):
        if self.has(pid):
            return self._registry[pid].result()
        return None

        
    def status(self, pid):
        return self._registry[pid].status()
    
    def allMessages(self, pid):
        return self._registry[pid].messages()
    
    def has(self,pid):
        return  pid in self._registry
    
    def delete(self,pid):
        if pid in self._registry:
            del self._registry[pid]
            
    def deleteBefore(self,timestr):
        from pyrest.deltat import parse_time
        
        try:
            nmess = len(self._registry)
            td = parse_time(timestr)
            latest = datetime.datetime.now() - td
            while not self._cleanupBefore(latest):
                time.sleep(1)
            
            nmess2 = len(self._registry)
            return  nmess - nmess2
        except Exception as a:
            # not doing anything with it .. ?
            raise a
        return 0
            
            
    def all(self):
        aall = []
        for k in self._registry:
            obj = self._registry[k]
            aall.append({"process":k,"running":not obj.closed})

        return aall
    



'''

 simple base handler to drop into the rest API callable endpoint
 
 NOTE - the clients expect that the return is always a dict including a 'success' flag, so {"somekey":data, "success":True}
'''
class BaseHandler(Routable):
    '''
    
    The base handler that adds access to the message store, add the following to the extending class to 
    make calls avai;able in inheriting class
     
    
    get_last_message = super().get_last_message
    get_messages = super().get_messages
    get_messages_all = super().get_messages_all
    delete_message = super().delete_message
    delete_messages_before = super().delete_messages_before
    get_ended = super().get_ended
    get_results = super().get_results
    
    
    '''
    
    
    def __init__(self, props):
        super().__init__() # otherwise this will fail 
        print("Init handler ...", file=sys.stderr, flush=True)
        self._properties = props
        if "file-config" in props:
            configpath = os.path.expandvars(props["file-config"])
            print (f"using config collection {configpath}")
            if "config-history" in props:
                try:
                    
                    fdname = mergeJsonFiles(os.path.expandvars(props["file-config"]))
                    p = pathlib.Path(fdname)
                    p.rename(props["config-history"])
                except Exception as e:
                    print(f"creating history config faild {e}")
                    
            os.environ["FILE_CONFIG"] = configpath
            os.environ["OP_MODE"] = "file"


            
    @get('/test', response_model= Any)
    def get_test(self) :
        try:
            with stopwatch("get'/test"):
                return {"context":self._properties["context"],
                        "success":True}
        except Exception as e:
            return {"error":str(e),"success":False}
        
    @get('/messages/status/{messageid}', response_model= Any)
    def get_last_message(self, messageid:str = Path(..., alias='messageid')) :
        
        with stopwatch("get'/messages/status"):
            
            if MessageStore.getInstance().has(messageid):
                msg, lmod, running = MessageStore.getInstance().status(messageid)
                return {"success":True,"message":msg,"lastMod":lmod,"running":running,"context":self._properties["context"]}
            
        return {"success":False,"message":"identifier does not exist","lastMod":None,"running":None,"context":self._properties["context"]}
    
    @get('/messages/message/{messageid}', response_model= Any)
    def get_messages(self, messageid:str = Path(..., alias='messageid')) :
        
        with stopwatch("get'/messages/message"):
            if MessageStore.getInstance().has(messageid):
                msg, lmod, running = MessageStore.getInstance().allMessages(messageid)
                return {"success":True,"message":msg,"lastMod":lmod,"running":running,"context":self._properties["context"]}
            
            return {"success":False,"message":"identifier does not exist","lastMod":None,"running":None,"context":self._properties["context"]}
        
    @get('/messages/all', response_model= Any)
    def get_messages_all(self) :
        
        with stopwatch("get'/messages/all"):
            return {"success":True,"messages":MessageStore.getInstance().all(),"context":self._properties["context"]}
            
        return {"success":False,"message":"request failed","context":self._properties["context"]}
        
        
    @delete('/messages/message/{messageid}', response_model= Any)
    def delete_message(self, messageid:str = Path(..., alias='messageid')) :
        with stopwatch("delete'/messages/message"):
            if MessageStore.getInstance().has(messageid):
                MessageStore.getInstance().delete(messageid)
                return {"success":True,"messages":"deleted","context":self._properties["context"]}
                
            return {"success":False,"messages":"does not exist","context":self._properties["context"]}
        
    @delete('/messages/before/{timestr}', response_model= Any)
    def delete_messages_before(self, timestr:str = Path(..., alias='timestr')) :
        with stopwatch("delete'/messages/before"):
            try:
                ndel = MessageStore.getInstance().deleteBefore(timestr)
                return {"success":True,"messages":f"deleted {ndel}","context":self._properties["context"]}
            except Exception as a: 
                return {"success":False,"messages":f"delete failed '{a}'","context":self._properties["context"]}
          
    
    @get('/messages/ended/{messageid}', response_model= Any)
    def get_ended(self, messageid:str = Path(..., alias='messageid')) :
        
        if MessageStore.getInstance().has(messageid):
            return {"success":True,"ended":MessageStore.getInstance().processEndedNormaly(messageid),"context":self._properties["context"]}
        
        return {"success":False,"ended":None,"context":self._properties["context"]}


    @get('/messages/results/{messageid}', response_model= Any)
    def get_results(self, messageid:str = Path(..., alias='messageid')) :
        
        if MessageStore.getInstance().has(messageid):
            return {"success":True,"results":MessageStore.getInstance().processResults(messageid),"context":self._properties["context"]}
        
        return {"success":False,"results":None,"context":self._properties["context"]}
    
            