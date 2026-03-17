import importlib, os
import numpy as np 
from abc import abstractmethod
from copy import deepcopy

'''


requires configuration as

{'container";{
    "type":<entries from container map>
    "args":{ <dict of arguments for type class>
        "filepath":"/app/data/netcdf.nc", 
        "varnames":[],
        "coordinatenames":["lon","lat"] <correct where needed > 
        }

},
"match-keys":{
    "lon":<the matching variable name for longitude>
    "lat":<the matching variable name for latitude>
    
},
"context-keys":[
    "value":<the key returned for the value found>
    "context":<additional key values returned >
}


'''

def extractNOOP(res):
    return res

def createNetCDFDS(filepath,mode='r'):
    from netCDF4 import Dataset as DS
    ds =   DS(filepath,mode=mode)
    
    def extract(rs):
        from numpy.ma import getdata
        return getdata(rs).item()

    return ds,extract

def createNetCDFXA(filepath,mode='r'):
    import xarray as xr
    ds = xr.open_dataset(filepath,mode=mode)
    ds.load()
    
    def extract(rs):
        return rs.data.item()
    
    return ds,extract
    
    
createNetCDF = createNetCDFXA

def find_closest_idx(arr, val):
    # expects a numpy sorted array and single value 
    idx = np.searchsorted(arr , val)
    if idx +1 >=  arr.shape[0]: 
        return idx
    diff2 = (arr[idx+1] - arr[idx]) /2
    if val > arr[idx] + diff2:
        return idx+1
    
    return idx

def contains(bbox, x, y):
    return bool(bbox[0] <= x and 
                bbox[1] <= y and 
                bbox[2] >= x and 
                bbox[3] >= y)  


class Container():
    
    def __init__(self,varnames, coordinatenames = ["lon","lat"]):
        self._coordinates = coordinatenames
        self.vars = varnames
    
    @abstractmethod
    def getValueAt(self,idx,idy):
        raise NotImplementedError()
    
    @abstractmethod  
    def getXY1D(self):
        raise NotImplementedError()
    
    @abstractmethod  
    def getXY2D(self):
        raise NotImplementedError()
    
    @abstractmethod  
    def inside(self,x,y):
        raise NotImplementedError()
    
    
'''
Cater for the 1/2 xy z/t dimensional coordinates, 1-3 dimensions for variable space

'''
        
class NetCDFContainer1D(Container):
    
    def __init__(self,filepath, varnames, coordinatenames = ["lon","lat"],**kwargs):
        Container.__init__(self, varnames, coordinatenames)
        
        
        ds,func =  createNetCDF(filepath)
        
        self._ds = ds
        self._extract = func
        
        self._mins = [self._ds[self._coordinates[0]][0],self._ds[self._coordinates[1]][0]]
        self._maxs = [self._ds[self._coordinates[0]][-1],self._ds[self._coordinates[1]][-1]]
        
        print(f"NetCDFContainer1D loaded {filepath}")
        
    def getXY1D(self):
        return self._ds[self._coordinates[0]][:],self._ds[self._coordinates[1]][:]
    
    def inside(self,x,y):
        return contains([*self._mins,*self._maxs],x,y)
        '''
        #print("{} {} {} {}".format(self._mins[0] < x,))
        return bool(self._mins[0] < x and 
                self._maxs[0] > x and
                self._mins[1] < y and 
                self._maxs[1] > y )
        '''
        
    
    def getValueAt(self,idx,idy):
        return [self._extract(self._ds[v][idy,idx]) for v in self.vars]
        
            
    def finalise(self):
        if self._ds:
            self._ds.close()
            self._ds = None
            self._mins = None
            self._maxs = None
            
            
            
class NetCDFConatinerMap(Container):
    
    class NetcdfTile(Container):
        def __init__(self, props, rootpath):
            self._bbox = props['bbox']
            Container.__init__(self, props["varnames"],props["coordinatenames"])
            self._fpath = os.path.join(rootpath,props["filepath"])

            ds, func = createNetCDF(self._fpath)
            
            self._ds = ds
            self._exract = func
        
        def inside(self,x,y):
            return contains(self._bbox, x, y)
            
        
            
    
    def __init__(self,filepath, **kwargs):
        import json
        with open (filepath,'r') as fp:
            self._props = json.load(fp)
        
        Container.__init__(self, self._props["varnames"],self._props["coordinatenames"])
        
        
        self._mins = self._props["bbox"][:2]
        self._maxs = self._props["bbox"][2:]
        
        self._tiles = []
        nj =  len(self._props["tiles"])
        ni =  len(self._props["tiles"][0])
        
        for j in  range(len(self._props["tiles"])):
            row = []
            for  t in self._props["tiles"][j]:
                row.append(NetCDFConatinerMap.NetcdfTile(t))
            self._tiles.append(row)
    
        
        
    
    
    def inside(self,x,y):
        return contains(self._props["bbox"], x, y)
    
    def getXY1D(self):
        pass
        
    
    
    def _findTile(self,x,y):
        for t in self._tiles:
            if t.inside( x,y):
                return t
            
        return None
    
    
        
            
containermap = {"netcdf1D":NetCDFContainer1D}

        

class NetcdfAssessment():
    '''' 
    consider assignment of a dem or the like to establish value at point
     
    '''
    
    def __init__(self,config):
        self.props = config
        
        props = self.props["container"]
        if not props["type"] in containermap:
            print("Missing container implementation container {} ".format(props["type"]))
            raise ValueError("Missing container implementation container '{}' for {}".format(props["type"],props["args"]))
        
        containerclass = containermap[props["type"]]
        self._container = containerclass(**props["args"])
        
        self._match_keys = self.props['match-keys']
        self._context_keys = self.props['context-keys']
        
        self._idxx = -1
        self._idxy = -1
        #self._assignx = -1
        
    @property
    def _requiredkeys(self):
        return self._match_keys.values()

                
    def __call__(self, key, bbody = None,query = None):
        '''
        Given the point query find the first geometry and return the properties
        
        '''
        print (f"received request {key} with {query}")
        if not query:
            return "Missing all query parameters!"
        
        q = {**query}
        if not all(k in q for k in self._requiredkeys ):
            return "Missing query parameters have {} need {}".format(q.keys(),self._requiredkeys)
        
        
        lat = float(q[self._match_keys["lat"]])
        lon = float(q[self._match_keys["lon"]])
        
        #??
        if "timestamp" in self._match_keys and self._match_keys["timestamp"] in q:
            ts = float(q[self._match_keys["timestamp"]])
        
        #  returns a list of values     
        value =  value2d(self._container,lon,lat)
        
        if isinstance(self._context_keys["value"],(list,tuple)):
            nkeys  = deepcopy(self.vars)
            # replace the ones we have references for
            for i,k,_ in enumerate(zip(self._context_keys["value"],self.vars)):
                nkeys[i] = k
                
            res = {k:v for k,v in zip(nkeys,value)}
            
        else:
            while isinstance(value,list) and len(value) == 1:
                value = value[0]
                
            res = {self._context_keys["value"]:value}
        if "context" in self._context_keys and self._context_keys["context"]:
            return {**res,**self._context_keys["context"]}
        
        return res


def value2d(container,x,y):
    
    if container.inside(x,y):
        lons,lats = container.getXY1D()
        ydx =  find_closest_idx(lats,y)
        xdx =  find_closest_idx(lons,x)
        print(f"found idx {xdx} idy {ydx}")
        return [container.getValueAt(xdx,ydx)]
    
    return []
    
    