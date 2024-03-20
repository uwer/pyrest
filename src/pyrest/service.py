import os, sys,time
import json
from classy_fastapi import ( Routable, 
                             get,  
                             put, post
                             )

from fastapi import Request,UploadFile,File,Path
from typing import Any

#from scipy.stats._discrete_distns import geom

'''
def maintest():
    import uvicorn
    from fastapi import FastAPI

    from qgisAPI3.delegates import APIDelegate
    
    app = FastAPI()
    routes = APIDelegate()
    # router member inherited from cr.Routable and configured per the annotations.
    app.include_router(routes.router)

    uvicorn.run(app,port=9888)
'''
    
    
class EchoHandler():
    
    def __init__(self, config):
        pass
    
    
    def __call__(self,key,bbody = None ,query = None, fileref = None):
        body = None
        q = {}
        if bbody:
            body = bbody.decode()
        
        if query:
            q  = query
            
        if fileref:
            if hasattr(fileref,'name'):
                try:
                    print ("received file like {}".format(fileref.name))
                except:
                    print ("received file reference {}".format(str(fileref)))
        
        print ("received query {}".format(q))
        res = {"key":key,"body":body if body else "","query":{**q} }
        
        try:
            if "wait" in q:
                time.sleep(float(q["wait"]))
            
        except :
            print ("wait failed")
        print ("received key {key} with body {body} and query {query}".format(**res))
        return res
        

class APIDelegate(Routable):
    
    
    def __init__(self, handler):
        super().__init__()
        
        '''
        handler has to be callable and take the request body and query string
        
        '''
        self._handler  = handler
    
    @post('/process', response_model= Any)
    def submit(self,request: Request = ...) :
        """
        launch a new process
        """
        from pyrest import stopwatch
        #print("submit  - {}".format(body))
        try:
            with stopwatch("process",""):
                return self._handler('process',request.body,request.query_params())
    
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return None
        
    @get('/lookup', response_model=Any)
    def lookup(self,request: Request = ...) :
        """
        lookup against handler 
        """
        from pyrest import stopwatch
        #print("lookup  - {} ".format(request))
        try:
            with stopwatch("lookup",""):
                return self._handler('lookup',None,request.query_params)
    
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return None
        
        

    @put('/process/data', response_model=None)
    async def  set_data(self,
        request: Request = ...
    ) -> None:
        
        
        """
        set data handler 
        """
        from pyrest import stopwatch
        #print("lookup  - {} ".format(request))
        try:
            with stopwatch("put data",""):
                data = await request.body()
                return self._handler('data',data,request.query_params)
    
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return None
    
    
    
    @post('/process/data', response_model=None)
    def upload_file(self,
        upload_file: UploadFile = File(...)
    ) -> None:
        """
        set the processes data file
        """
        try:
            from pyrest import stopwatch
            import tempfile
            with stopwatch("upload data",""):
                #in_file.filename
                fd = tempfile.NamedTemporaryFile(prefix=upload_file.filename,delete=False)
                print("temp file at {} ".format(fd.name))
                #print(" type uf {} ".format(type(upload_file)))
                content = upload_file.file.read(1024)
                while content :  # async read chunk
                    #print(content)
                    fd.write(content)
                    content = upload_file.file.read(1024)
                fd.seek(0)
                return self._handler('data',fd)
            


        finally:
            upload_file.file.close()

        return None
        
        
def _class(class_str):
    """
    Return a class reference from a string
    
    """
    #import traceback
    class_str = class_str.strip()
    lidx = class_str.rfind(".")
    module_name = ""
    class_name = class_str
    if lidx > 0:
        module_name = class_str[:lidx]
        class_name = class_str[lidx+1:]
        
    try:
        from pydoc import locate
        class_ = locate(class_str)
        if not class_:
            import importlib
            module_ = importlib.import_module(module_name)
            try:
                class_ = getattr(module_, class_name)()
                class_ = type(class_)
            except Exception as ae:
                print('Class does not exist {}'.format(ae))
    except Exception as ie:
        import traceback
        print(traceback.extract_stack(ie))
        traceback.print_stack()
        print('Module load error: {}'.format(ie))
        
    return class_ or None
    
def _instanceFromConfig(config):
    '''
    mandatory keys 
    "instance":{"class":<string>}
    "config":{<whatever the instance needs>}
    
    '''
    clazz =_class(config["instance"]["class"])
    if not clazz:
        raise ValueError("could not create {}".format(config))
    
    return clazz(config["config"])


def app():
    '''
    The UVICORN entry point
    
    '''

    try:
        
        from fastapi import FastAPI
        
        
        app = FastAPI()
        
        with open(os.getenv('HANDLERCONFIG'),'r') as fp:
            config = json.load(fp)
        
        
        routes = APIDelegate(_instanceFromConfig(config))
        # router member inherited from cr.Routable and configured per the annotations.
        app.include_router(routes.router)
        return app
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

    
    
def main():
    ##This is only for testing !!!! 
    import uvicorn
    uvicorn.run(app(),host="0.0.0.0", port=int(float(os.getenv('HANDLERPORT','9088'))) )
    
    

if __name__ == "__main__":
    ##This is only for testing !!!! 
    __localdir = os.path.dirname(os.path.abspath(__file__))
    __localpdir = os.path.dirname(__localdir)
    print ("testing local path {}".format(__localpdir))
    if not __localpdir in sys.path:
        sys.path.append(__localpdir)
    
    
    if not 'HANDLERCONFIG' in os.environ:
        os.environ['HANDLERCONFIG'] = os.path.join(__localdir,"echo.json")
    
    
    main()
    
    