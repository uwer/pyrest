import  os
import numpy as np 
from abc import abstractmethod




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
        self.var = varnames
    
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
    
    def __init__(self,filepath, varnames, coordinatenames = ["lon","lat"]):
        Container.__init__(self, varnames, coordinatenames)
        from netCDF4 import Dataset as DS
        #DS = importlib.import_module("Dataset","netCDF4") 
        self._ds = DS(filepath,mode='r')
        
        self._mins = [self._ds[self._coordinates[0]][0],self._ds[self._coordinates[1]][0]]
        self._maxs = [self._ds[self._coordinates[0]][-1],self._ds[self._coordinates[1]][-1]]
        
    def getXY1D(self):
        return self._ds[self._coordinates[0]][:],self._ds[self._coordinates[1]][:]
    
    def inside(self,x,y):
        #print("{} {} {} {}".format(self._mins[0] < x,))
        return bool(self._mins[0] < x and 
                self._maxs[0] > x and
                self._mins[1] < y and 
                self._maxs[1] > y )
        
        
    
    def getValueAt(self,idx,idy):
        from numpy.ma import getdata
        #res = getdata(self._ds[self.var][idy,idx])
        #return res.item()
    
        return [getdata(self._ds[v][idy,idx]).item() for v in self.vars]
        
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
            Container.__init__(self, props["varname"],props["coordinatenames"])
            self._fpath = os.path.join(rootpath,props["filepath"])
            self._ds = None
        
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
        for t in  self._props["tiles"]:
            self._tiles.append(NetCDFConatinerMap.NetcdfTile(t))
    
    
    def _findTile(self,x,y):
        for t in self._tiles:
            if t.inside( x,y):
                return t
            
        return None
        
            
containermap = {"netcdf":NetCDFContainer1D}

        

class NetcdfAssessment():
    '''' 
    consider assignment of a dem or the like to establish elevation at point
     
    '''
    
    def __init__(self,progressHandler,**kwargs):
        self.props = kwargs["properties"]
        self._progressHandler = progressHandler
        
        props = self.props_eval["data"]
        if not props["container"] in containermap:
            print("Missing container implementation container {} ".format(props["container"]))
            raise ValueError("Missing container implementation container '{}' for {}".format(props["container"],props["filename"]))
        
        containerclass = containermap[props["container"]]
        self._container = containerclass(**props)
        
        self._match_keys = props['match-keys']
        
        self._idxx = -1
        self._idxy = -1
        #self._assignx = -1
        
    @property
    def _requiredkeys(self):
        return self._match_keys.values()

                
    def __call__(self,key,bbody = None,query = None):
        '''
        Given the point query find the first geometry and return the properties
        
        '''
        if not query:
            return ValueError("missing all query parameters")
        
        q = {**query}
        if not all(k in q for k in self._requiredkeys ):
            return ValueError("Missing query parameters have {} need {}".format(q.keys(),self._requiredkeys))
        
        
        lat = float(q[self._match_keys["lat"]])
        lon = float(q[self._match_keys["lon"]])
        #if 
        ts = float(q[self._match_keys["timestamp"]])
        
        


def value2d(container,x,y):
    
    if container.inside(x,y):
        lons,lats = container.getXY1D()
        ydx =  find_closest_idx(lats,y)
        xdx =  find_closest_idx(lons,x)
        return [container.getValueAt(xdx,ydx)]
    
    return []
    
    