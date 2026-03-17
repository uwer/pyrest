import shapely
import pyproj

class BufferFactory():
    
    _instance = None
    
    @staticmethod 
    def instance():
        # if this is called while none, we have an application error and wrong init 
        if not BufferFactory._instance:
            BufferFactory._instance = BufferFactory()
        
        return BufferFactory._instance
    
    
    
    def __init__(self):
        from geographiclib.geodesic import Geodesic
        self.geodesic = Geodesic
        
        self.epsg4326Proj = pyproj.CRS('epsg:4326')
    
    def lookupUTM(self,lon, lat) :
        # find the UTM zone for a coordinate
        if lat >= 72.0 and lat < 84.0:
            if lon >= 0.0 and lon < 9.0:
                return 31
            if lon >= 9.0 and lon < 21.0:
                return 33
            if lon >= 21.0 and lon < 33.0:
                return 35
            if lon >= 33.0 and lon < 42.0:
                return 37
        if lat >= 56 and lat < 64.0 and lon >= 3 and lon <= 12:
            return 32
        
        zone = round((lon + 180) / 6) 
        return zone if lat >= 0 else zone  * -1
        
    def findEPSGFromZone(self,zone) :
        
        #zone = getZones(longitude, latitude)   
        epsg_code = 32600
        epsg_code += int(abs(zone))
        if (zone < 0): # South
            epsg_code += 100    
        return epsg_code
    

    def distance (self,p1,p2):
        #return  Geodesic.WGS84.Inverse(39.435307, -76.799614, 39.43604, -76.79989)
        return  self.geodesic.WGS84.Inverse(p1.y, p1.x, p2.y, p2.x)['s12']

    def distanceList(self,points):
        dlist = []
        for i in range(1,len(points)):
            dlist.append(self.distance(points[i-1],points[i]))
            
        return dlist
        
        
    
    def bearing (self,p1,p2):
        return self.geodesic.WGS84.Inverse( p1.y, p1.x, p2.y, p2.x)['azi1']
    
    def bearingProb(self,p1,p2,p3):
        b1 = self.bearing(p1,p2)
        b3 = self.bearing(p1,p3)
        return b1, b3 , b1 / b3
    
    
    
    def distanceAtBearing (self, p1, bearing, distance_m):
        resdict = self.geodesic.WGS84.Direct( p1.y, p1.x, bearing, distance_m) 
        return shapely.Point(resdict ['lon2'],resdict ['lat2'])


    def bufferSpherical(self,p1, distance_m): 
        # this should be less than 10 km, otherwise too much distortion
        from shapely.ops import transform
        epsg = self.findEPSGFromZone(self.lookupUTM(p1.x,p1.y))
        proj = pyproj.CRS('epsg:{}'.format(epsg))
        
        project = pyproj.Transformer.from_crs(self.epsg4326Proj, proj, always_xy=True).transform
        p1p = transform(project, p1)
        ppbuffer = p1p.buffer(distance_m)
        project2 = pyproj.Transformer.from_crs(proj,self.epsg4326Proj, always_xy=True).transform
        buffer =  transform(project2,ppbuffer)
        return buffer

class Geometries():
    '''
    Collection of Geometries
    
    '''
    
    class Geometry():
        
        def __init__(self, geom, props):
            self.geom = geom
            self.properties = props
            
            
        @property
        def centroid(self):
            return self.geom.centroid
        
        @property
        def geometry(self):
            return self.geom
        
        
        def inside(self, point):
            return self.geom.contains(point)
            
    
    def __init__(self,config):
        self._geoms = []
        self._tree = None
        
        ## load the geometries
        
        from pathlib import Path
        
        pp = Path(config["geometries"])
        if pp.exists():
            import fiona
            from shapely.geometry import shape
            if pp.is_file():
                for c in iter(fiona.open(str(pp),'r')):
                    self.append(Geometries.Geometry(shape(c["geometry"]), c["properties"]))
            
            elif pp.is_dir():
                geomspath = pp.glob("*")
                self._collectGeoms(geomspath)
        else:
            raise ValueError("No valid geometries provided")
        
        if "lookup" in config and len(config["lookup"]) > 0:
            import pandas
            self._lookup = {}
            for k in config["lookup"]:
                self._lookup[k] = pandas.read_csv(config["lookup"][k]) 
        else:
            self._lookup = None
        self._match_keys = config['match-keys']
        self._required = config.get('required',{k:self._match_keys[k].values() for k in self._match_keys})
        self._distance = config.get('distance',10000.)
        predicate = config.get('predicate',"intersection")
        self._predicate = self.intersections
        if "nearest" == predicate:
            self._predicate = self.nearest
        self._init()
        
    def _collectGeoms(self,geomspath):
        import fiona
        from shapely.geometry import shape
        for g in geomspath:
            nn = g.stem
            pname = nn.split("-")
            n = "".join(pname[:-1])
            d = pname[-1]
            for c in iter(fiona.open(str(g),'r')):
                self.append(Geometries.Geometry(shape(c["geometry"]),c["properties"]))
                
    @property
    def _requiredkeys(self):
        return self._required
        
    def append(self, geom ):
        if self._tree:
            return
        self._geoms.append(geom)
        

        
        
    def _init(self):
        if self._tree:
            return
        
        try:
            from shapely import STRtree
        except :
            from shapely.strtree import STRtree
            
        self._tree = STRtree([g.geom for g in self._geoms])
        print("stree  count {}".format(len(self._tree)))
        
        
    def intersections(self, geom0):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate='intersects')
        return [self._geoms[i] for i in indices]
    
    
    def closestPoint(self, geom0,distance=10000):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate='dwithin' , distance=distance)
        
        res = [self._geoms[i] for i in indices]
        from shapely.ops import nearest_points
        
        p1, p2 = nearest_points([g.geom for g in res], geom0)
        
        return p1 
    
    def nearest(self, geom0,predicate='dwithin',distance=10000):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate=predicate , distance=distance)
        
        if indices is  None or len(indices) == 0:
            return None,None
        
        res = [self._geoms[i] for i in indices]
        from shapely.ops import nearest_points
        
        p1, p2 = nearest_points([g.geom for g in res], geom0.centroid)
        
        distances = []
        for p11 in p1:
            distances.append(BufferFactory.instance().distance(p11,geom0.centroid))
            
        minp = min(distances)
        min_idx = distances.index(minp)
        
        return minp, res[min_idx]
    
    
    def __call__(self,key,bbody = None,query = None, fileref = None):
        '''
        Given the point query find the first geometry and return the properties
        
        '''
        if not query:
            return "missing all query parameters"
        
        q = {**query}
        if key in self._requiredkeys:
            if not all(k in q for k in self._requiredkeys[key] ):
                return "Missing query parameters have {} need {}".format(q.keys(),self._requiredkeys[key])
            
        if key == 'search':
            from shapely.geometry import Point
            from fiona.model import to_dict
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                return to_dict(intersections[0].properties)
            
            if "buffer" in self._match_keys[key] and self._match_keys[key]["buffer"] in q:
                pbufffer = BufferFactory.instance().bufferSpherical(p,float(q[self._match_keys[key]["buffer"]]))
                minp,geom = self.nearest(pbufffer,predicate="intersects")
                if geom:
                    return to_dict(geom.properties)
                #intersections = self._predicate(pbufffer)
                #if intersections:
                #    return intersections[0].properties
                #p11,p22, geoms = self.nearest (p,distance=float(q[self._match_keys["buffer"]]))
                
                
            return {}
        elif key =="raw":
            from shapely.geometry import Point
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                return shapely.to_wkt(intersections[0].geom)
            
            return None
            
        
        elif key == 'lookup':
            '''
            Return a list of matching records, subset by the keys associated with the match key
            '''
            
            if not self._lookup:
                return []
            
            matchkeys = list(self._match_keys[key])
            matchkey = None
            for k in matchkeys:
                if k in q:
                    matchkey = k
                    break
                
            if not matchkey:
                return f"No match key found for request {key} - available keys {matchkeys}"
            
            matchvalue = q[matchkey]
            
            if self._lookup and matchkey in self._lookup and matchkey in self._lookup[matchkey].columns:
                from pandas.api.types import is_numeric_dtype
                pdf = self._lookup[matchkey]
                
                if is_numeric_dtype(pdf[matchkey]):
                    try:
                        matchvalue = float(matchvalue)
                    except:
                        raise f"Attempting to lookup non-number against numeric column {matchvalue}"
                    
                df  = pdf[pdf[matchkey] == matchvalue]
                
                if len(df.index) > 0:
                    keys = self._match_keys[key][matchkey]
                    return df.filter(items=keys).to_dict("Records")
        
                else:
                    return []
                
            else:
                
                for g in self._geoms:
                    if g.properties[matchkey] == matchvalue:
                        return dict(g.properties)
            
            return []
            
        else:
            return f"Do not understand request {key}"
        
"""

class Rasters():
    '''
    Collection of Geometries
    
    '''
    
    class Raster():
        
        def __init__(self, raster, props):
            self.raster = raster
            self.properties = props
            
            
        @property
        def centroid(self):
            return self.raster.centroid
        
        @property
        def geometry(self):
            return self.geom
        
        
        def inside(self, point):
            return self.geom.contains(point)
            
    
    def __init__(self,config):
        self._rasters = []
        
        

        
        ## load the geometries
        
        from pathlib import Path
        
        pp = Path(config["rasters"])
        if pp.exists():
            import fiona
            from shapely.geometry import shape
            if pp.is_file():
                for c in iter(fiona.open(str(pp),'r')):
                    self.append(Geometries.Geometry(shape(c["geometry"]), c["properties"]))
            
            elif pp.is_dir():
                geomspath = pp.glob("*")
                self._collectGeoms(geomspath)
        else:
            raise ValueError("No valid geometries provided")
        
        if "lookup" in config and len(config["lookup"]) > 0:
            import pandas
            self._lookup = {}
            for k in config["lookup"]:
                self._lookup[k] = pandas.read_csv(config["lookup"][k]) 
        else:
            self._lookup = None
        self._match_keys = config['match-keys']
        self._required = config.get('required',{k:self._match_keys[k].values() for k in self._match_keys})
        self._distance = config.get('distance',10000.)
        predicate = config.get('predicate',"intersection")
        self._predicate = self.intersections
        if "nearest" == predicate:
            self._predicate = self.nearest
        self._init()
        
    def _collectGeoms(self,geomspath):
        import fiona
        from shapely.geometry import shape
        for g in geomspath:
            nn = g.stem
            pname = nn.split("-")
            n = "".join(pname[:-1])
            d = pname[-1]
            for c in iter(fiona.open(str(g),'r')):
                self.append(Geometries.Geometry(shape(c["geometry"]),c["properties"]))
                
    @property
    def _requiredkeys(self):
        return self._required
        
    def append(self, geom ):
        if self._tree:
            return
        self._geoms.append(geom)
        


        
        
    def intersections(self, geom0):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate='intersects')
        return [self._geoms[i] for i in indices]
    
    
    def closestPoint(self, geom0,distance=10000):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate='dwithin' , distance=distance)
        
        res = [self._geoms[i] for i in indices]
        from shapely.ops import nearest_points
        
        p1, p2 = nearest_points([g.geom for g in res], geom0)
        
        return p1 
    
    def nearest(self, geom0,predicate='dwithin',distance=10000):
        
        if not self._tree:
            raise ValueError("Geometries not initialised")
    
        indices = self._tree.query(geom0,predicate=predicate , distance=distance)
        
        if indices is  None or len(indices) == 0:
            return None,None
        
        res = [self._geoms[i] for i in indices]
        from shapely.ops import nearest_points
        
        p1, p2 = nearest_points([g.geom for g in res], geom0.centroid)
        
        distances = []
        for p11 in p1:
            distances.append(BufferFactory.instance().distance(p11,geom0.centroid))
            
        minp = min(distances)
        min_idx = distances.index(minp)
        
        return minp, res[min_idx]
    
    
    def __call__(self,key,bbody = None,query = None, fileref = None):
        '''
        Given the point query find the first geometry and return the properties
        
        '''
        if not query:
            return ValueError("missing all query parameters")
        
        q = {**query}
        if key in self._requiredkeys:
            if not all(k in q for k in self._requiredkeys[key] ):
                raise ValueError("Missing query parameters have {} need {}".format(q.keys(),self._requiredkeys[key]))
            
        if key == 'search':
            from shapely.geometry import Point
            from fiona.model import to_dict
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                return to_dict(intersections[0].properties)
            
            if "buffer" in self._match_keys[key] and self._match_keys[key]["buffer"] in q:
                pbufffer = BufferFactory.instance().bufferSpherical(p,float(q[self._match_keys[key]["buffer"]]))
                minp,geom = self.nearest(pbufffer,predicate="intersects")
                if geom:
                    return to_dict(geom.properties)
                #intersections = self._predicate(pbufffer)
                #if intersections:
                #    return intersections[0].properties
                #p11,p22, geoms = self.nearest (p,distance=float(q[self._match_keys["buffer"]]))
                
                
            return {}
        elif key =="raw":
            from shapely.geometry import Point
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                return shapely.to_wkt(intersections[0].geom)
            
            return None
            
        
        elif key == 'lookup':
            '''
            Return a list of matching records, subset by the keys associated with the match key
            '''
            
            if not self._lookup:
                return []
            
            matchkeys = list(self._match_keys[key])
            matchkey = None
            for k in matchkeys:
                if k in q:
                    matchkey = k
                    break
                
            if not matchkey:
                raise ValueError(f"No match key found for request {key} - available keys {matchkeys}")
            
            matchvalue = q[matchkey]
            
            if self._lookup and matchkey in self._lookup and matchkey in self._lookup[matchkey].columns:
                from pandas.api.types import is_numeric_dtype
                pdf = self._lookup[matchkey]
                
                if is_numeric_dtype(pdf[matchkey]):
                    try:
                        matchvalue = float(matchvalue)
                    except:
                        raise ValueError(f"Attempting to lookup non-number against numeric column {matchvalue}")
                    
                df  = pdf[pdf[matchkey] == matchvalue]
                
                if len(df.index) > 0:
                    keys = self._match_keys[key][matchkey]
                    return df.filter(items=keys).to_dict("Records")
        
                else:
                    return []
                
            else:
                
                for g in self._geoms:
                    if g.properties[matchkey] == matchvalue:
                        return dict(g.properties)
            
            return []
            
        else:
            raise ValueError(f"Do not understand request {key}")
        

"""
    
class TimeZones(Geometries):


    def __call__(self,key,bbody = None,query = None, fileref = None):
        '''
        Given the point query find the first geometry and return the properties
        
        '''
        import  pytz
        if not query:
            return ValueError("missing all query parameters")
        
        q = {**query}
        if key in self._requiredkeys:
            if not all(k in q for k in self._requiredkeys[key] ):
                return ValueError("Missing query parameters have {} need {}".format(q.keys(),self._requiredkeys[key]))
            
        if key == 'search':
            from shapely.geometry import Point
            #from fiona.model import to_dict
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            timezone_str = None
            
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                timezone_str = intersections[0].properties["tzid"]
                
                
            
            if "buffer" in self._match_keys[key] and self._match_keys[key]["buffer"] in q:
                pbufffer = BufferFactory.instance().bufferSpherical(p,float(q[self._match_keys[key]["buffer"]]))
                minp,geom = self.nearest(pbufffer,predicate="intersects")
                if geom:
                    timezone_str = geom.properties["tzid"]

            if timezone_str:
                timezone = pytz.timezone(timezone_str)
                return {"timezone":timezone_str,"offset":timezone._utcoffset}
                
            return {}
        
            """
        elif key =="raw":
            from shapely.geometry import Point
            
            lat = float(q[self._match_keys[key]["lat"]])
            lon = float(q[self._match_keys[key]["lon"]])
            p = Point(lon,lat)
            intersections = self._predicate(p)
            if intersections:
                return shapely.to_wkt(intersections[0].geom)
            
            return None
            
          
        elif key == 'lookup':
            '''
            Return a list of matching records, subset by the keys associated with the match key
            '''
            matchkeys = list(self._match_keys[key])
            matchkey = None
            for k in matchkeys:
                if k in q:
                    matchkey = k
                    break
                
            if not matchkey:
                raise ValueError(f"No match key found for request {key} - available keys {matchkeys}")
            
            matchvalue = q[matchkey]
            
            if self._lookup and matchkey in self._lookup and matchkey in self._lookup[matchkey].columns:
                from pandas.api.types import is_numeric_dtype
                pdf = self._lookup[matchkey]
                
                if is_numeric_dtype(pdf[matchkey]):
                    try:
                        matchvalue = float(matchvalue)
                    except:
                        raise ValueError(f"Attempting to lookup non-number against numeric column {matchvalue}")
                    
                df  = pdf[pdf[matchkey] == matchvalue]
                
                if len(df.index) > 0:
                    keys = self._match_keys[key][matchkey]
                    return df.filter(items=keys).to_dict("Records")
        
                else:
                    return []
                
            else:
                
                for g in self._geoms:
                    if g.properties[matchkey] == matchvalue:
                        return dict(g.properties)
            
            return []
            
            """
        else:
            raise ValueError(f"Do not understand request {key}")
        
        
            