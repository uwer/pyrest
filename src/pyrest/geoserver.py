'''

register services with geoserver 
i.e. postgis layers for local datastores to server WFS

connect to external WFS 
  
'''
from pyrest.rest import ApiClient
from pyrest.configuration import Configuration
from copy import deepcopy
from pyrest import logme, ensureURLPath
from six.moves.urllib.parse import quote

import sys,json

templatePostgisStore = {
  "dataStore": {
    "name": "",
    "connectionParameters": {
      "entry": [
        {"@key":"dbtype","$":"postgis"},
         {
                    "@key": "Expose primary keys",
                    "$": "true"
                },
                {
                    "@key": "validate connections",
                    "$": "true"
                },{
                    "@key": "schema",
                    "$": "public"
                },
                
      ]
    }
  }
}
'''
        {"@key":"host","$":""},
        {"@key":"port","$":"5432"},
        {"@key":"database","$":""},
        {"@key":"user","$":""},
        {"@key":"passwd","$":""},
'''

feturetypeinfo_template={
  "name": "poi",
  "nativeName": "poi",
  "title": "",
  "namespace": {},
  "abstract": "",
  "keywords": { "string": [] },
  "metadataLinks": {"metadataLink": []},
  "dataLinks": {"org.geoserver.catalog.impl.DataLinkInfoImpl": [ ] },
  "srs": "EPSG:4326",
  "projectionPolicy": "REPROJECT_TO_DECLARED",
  "enabled": True,
  "metadata": {"entry": [
      {"@key": "kml.regionateStrategy",
        "$": "external-sorting"},
      {"@key": "kml.regionateFeatureLimit",
       "$": "15"},
      {"@key": "cacheAgeMax",
        "$": "3000"},
      {"@key": "cachingEnabled",
        "$": "true"},
      {"@key": "kml.regionateAttribute",
       "$": "NAME"}
    ]},
  "cqlFilter": "INCLUDE",
  "maxFeatures": 10000,
  "numDecimals": 3,
  "responseSRS": { "string": [4326] },
  "overridingServiceSRS": True,
  "skipNumberMatched": True,
  "attributes": {"attribute": [{
        "name": "the_geom",
        "minOccurs": 0,
        "maxOccurs": 1,
        "nillable": True
        
      },
      {},
      {},
      {}]}
}
bbox_dummy = {"minx":115.1689999999999969,
                  "maxx":121.2570000000000050,
                  "miny":-13.0000000000000000,
                  "maxy":-8.7349999999999994,
                  "crs": "EPSG:4326"}


time_dim_enable_XML = ['<coverage><name>','</name><enabled>true</enabled><metadata><entry key="time"><dimensionInfo><enabled>true</enabled><presentation>LIST</presentation><units>ISO8601</units></dimensionInfo></entry></metadata></coverage>']




def _layersForService(service, xmltree):
    su = service.upper()
    if "WFS" == su:
        layerparent = ["FeatureTypeList","FeatureType"]
    elif "WMS" == su:
        layerparent = ["Capability","Layer","Layer"]
    elif "WCS" == su:
        layerparent = ["wcs:Capability","wcs:Request","wcs:GetCoverage"]


    #elements = xmltree.findall(".//*[@name='{}']/{}".format(layerparent[-2],layerparent[-1]))
    elements = xmltree.findall("/".join(layerparent))
    print (elements)
    
def validateOWSURL(ows,service):
    # ows is no longer a valid path, so make sure we replace it
    if ows.endswith("ows"):
        ows = ows[:-3]
    elif ows.endswith("ows/"):
        ows = ows[:-4]
    
    elif ows.endswith(service):
        return ows
    
    if ows.endswith("/"):
        return "{}{}".format(ows,service)
    
    return "{}/{}".format(ows,service)
    
    
    
def _versionForService(service):    
    su = service.upper()
    if "WFS" == su:
        return "2.0.0"
    
    if "WMS" == su:
        return "1.3.0"
    
    if "WCS" == su:
        return "1.1.1"
    
    if "WPS" == su:
        
        return "1.0.0"
    
    
contenttypes = {"gpkg":{"Content-Type":"application/x-sqlite3"},
                "style-sld":{"Content-Type":"application/vnd.ogc.sld+xml"},
                "style-se":{"Content-Type":"application/vnd.ogc.sld+xml"},
                "xml":{"Content-Type":"text/xml"},
                "accept-json":{"accept":"application/json"},
                "json":{"Content-Type":"application/json"},
                "zip":{"Content-Type":"application/zip"},
                }



def contentType4suffix(suffix):
    s = str(suffix).lower()
    if '.zip' == s:
        return contenttypes["zip"]
    if '.gpkg' == s:
        return contenttypes["gpkg"]
    
    if '.xml' == s:
        return contenttypes["xml"]
    
    if '.sld' == s:
        return contenttypes["style-sld"]
    
    
    if '.json' == s or ".geojson" == s:
        return contenttypes["json"]
    
    
    return None
    
    
def _buildCreatePGStore(connection):
    pgstore = deepcopy(templatePostgisStore)
    pgcon = pgstore["dataStore"]["connectionParameters"]["entry"]
    for k in connection:
        pgcon.append({"@key":k,"$":str(connection[k])})
    
    return pgstore
    
    
        
        
class GSAPIClient(ApiClient):
    
    def __init__(self,apiconnection):
        self._apiconnection = apiconnection
       
        self.configuration = Configuration()
        self.configuration.host = self._apiconnection["url"]
        self.configuration.verify_ssl = False
        self.configuration.setTimeout(10,60)
        #self.configuration.connection_pool_maxsize = 2
        #'content-type': 'application/json; charset=utf-8'
        ApiClient.__init__(self, self.configuration,maxpool=2)# this is the default ,header_name='content-type', header_value='application/json; charset=utf-8')
        
        #,self._query_api_key_name:_query_api_key

        # crude but easier ...
        import  httpx
        #._config import Timeout
        self.__rawclient = httpx.Client(timeout=httpx._config.Timeout(timeout=20.0))
        
        
    
        
    def _printConnection(self):
        logme("API {}".format(self._apiconnection))
        
    def call_api(self, resource_path, method,
                 path_params=None, query_params=None, header_params=None,
                 body=None, post_params=None, files=None,
                 response_type=object, auth_settings=None, async_req=None,
                 _return_http_data_only=True, collection_formats=None,
                 _preload_content=True, _request_timeout=None, _raise_error= False):
        
        if header_params:
            if not "accept" in header_params:
                header_params["accept"] = "application/json"
        else:
            header_params = {"accept":"application/json"}
            

            
        result = super().call_api(resource_path, method, 
                                  path_params, query_params, header_params, 
                                  body, post_params, files, response_type, 
                                  auth_settings, async_req, False, collection_formats, 
                                  _preload_content, _request_timeout, False)
        
        #print(result)
        if not 200 <= result[1] < 299:
            #print(result[0])
            print(f"received  failure code {result[1:]} on path {resource_path} {path_params} {result[0]}")
            if not _return_http_data_only:
                return  result[0]
            return None
        elif result[1] > 299: # this will never be called ....
            print(f"received error code {result[1:]} on path {resource_path} {path_params} {result[0]}")
            return None
        return  result[0]
    
    
    


    def getAvailableLayers(self):
        layers = self.call_api("layers", GSAPIClient.GET,query_params={self._query_api_key_name:self._query_api_key})
        return layers
    
    def getFeatureTypes(self, workspaceName):
        layers = self.call_api(f"/workspaces/{workspaceName}/featuretypes", GSAPIClient.GET)
        return layers
    

    def getFeatureTypesForStore(self, workspaceName,storeName):
        layers = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}/featuretypes", GSAPIClient.GET)
        return layers
    
    
    def getFeatureType(self, workspaceName,storeName,featureTypeName):
        layers = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}/featuretypes/{featureTypeName}", GSAPIClient.GET)
        return layers
     
    
    def getLayer(self, workspaceName,layerName):
        layers = self.call_api(f"/workspaces/{workspaceName}/layers/{layerName}", GSAPIClient.GET)
        return layers
    
    
    def createFeatureTypeOnDatastore(self, workspaceName,storeName,data):
        layers = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}/featuretypes", GSAPIClient.POST,body=data)
        return layers
    
    def createFeatureType(self, workspaceName,data,**kwargs):
        layers = self.call_api(f"/workspaces/{workspaceName}/featuretypes", GSAPIClient.POST,body=data,**kwargs)
        return layers
    
    def updateFeatureType(self, workspaceName,storeName,featureTypeName, data,**kwargs):
        layers = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}/featuretypes/{featureTypeName}", GSAPIClient.PUT,body=data,**kwargs)
        return layers
    
    
    def getFeatureStores(self,workspaceName):
        stores = self.call_api(f"/workspaces/{workspaceName}/datastores", GSAPIClient.GET)
        return stores
    
    def getFeatureStore(self,workspaceName,storeName):
        stores = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}", GSAPIClient.GET)
        return stores
    
    def updateFeatureStore(self,workspaceName,storeName, data):
        stores = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}", GSAPIClient.PUT,body=data)
        return stores
    
    
    def buildFeatureStoreAndType(self,workspaceName,storeName, zipdata, ftype = "shp", fname = "myshapefile.shp", headers = {"Content-Type":"application/zip"}, query = {"configure":"all"}):
        '''
        zipdata is binary data already!!!
        '''
        from pathlib import Path
        
        stores = self.call_api(f"/workspaces/{workspaceName}/datastores/{storeName}/file.{ftype}", GSAPIClient.PUT,
                               body=zipdata,header_params=headers,query_params=query)
        return stores


    def createFeatureStore(self,workspaceName, data):
        store = self.call_api(f"/workspaces/{workspaceName}/datastores", GSAPIClient.POST,body=data)
        return store
    
    def getCoverage(self, workspaceName,coverage):
        layers = self.call_api(f"/workspaces/{workspaceName}/coverages/{coverage}", GSAPIClient.GET)
        return layers
    
    def getCoverageForStore(self, workspaceName,storeName,coverage):
        layers = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages/{coverage}", GSAPIClient.GET)
        return layers
    
    
    def getCoverageExtensionForStore(self, workspaceName,storeName,coverage, extension, filter = {}):
        layers = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages/{coverage}/{extension}.json", GSAPIClient.GET, query_params=filter)
        return layers
    
    
    def getCoverageStores(self,workspaceName):
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores", GSAPIClient.GET)
        return stores
    
    def getCoverageStore(self,workspaceName,storeName):
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}", GSAPIClient.GET)
        return stores
    
    def updateCoverageStore(self,workspaceName,storeName, data):
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}", GSAPIClient.PUT,body=data)
        return stores
    
    def updateCoverage(self,workspaceName,storeName, data, headers = {"Content-Type":"text/xml"}):
        '''
         "Content-Type: text/xml" or
         'Content-Type: application/json'
         
         
        '''
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages", GSAPIClient.POST,body=data,header_params=headers)
        return stores
    
   
    
    
    def buildCoverageStoreAndType(self,workspaceName,storeName, rasterType, zipdata, headers = {"Content-Type":"application/zip"}, params = None):
        '''
        rasterType can be of imagemosaic, geotiff
        
        zipdata is binary data already!!!
        
        '''
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/file.{rasterType}", GSAPIClient.PUT,query_params = params,body=zipdata,header_params=headers)
        return stores


    def createCoverageStore(self,workspaceName, data):
        store = self.call_api(f"/workspaces/{workspaceName}/coveragestores", GSAPIClient.POST,body=data)
        return store
    
    def createCoverageProtoypeRemote(self,workspaceName, storeName,remotedata):
        store = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/remote.imagemosaic", GSAPIClient.POST,body=remotedata,header_params = {"Content-Type":"text/plain"})
        return store

    def configureCoverage(self,workspaceName, storeName,coveragexml):
        store = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages", GSAPIClient.POST,body=coveragexml,header_params = {"Content-Type":"text/xml"})
        return store
    
    def createCoverage(self,workspaceName, storeName,coveragejson):
        store = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages", GSAPIClient.POST,body=coveragejson)
        return store
    
    # styles
    def getStyles(self,workspace = None):
        if workspace:
            stores = self.call_api(f"/workspaces/{workspace}/styles", GSAPIClient.GET)
        else:
            stores = self.call_api(f"/styles", GSAPIClient.GET)
        return stores
        
        
    def getStyle(self,style,workspace = None):
        if workspace:
            stores = self.call_api(f"/workspaces/{workspace}/styles/{style}", GSAPIClient.GET)
        else:
            stores = self.call_api(f"/styles/{style}", GSAPIClient.GET)
        return stores
    
    
    def getLayerDefaultStyle(self,layer,workspace = None):
        if workspace:
            layerdat = self.call_api(f"/workspaces/{workspace}/layers/{layer}", GSAPIClient.GET)
        else:
            layerdat = self.call_api(f"/layers/{layer}", GSAPIClient.GET)
        if layerdat and "layer" in layerdat:
            return layerdat["layer"].get("defaultStyle",{})
        return {}
    
    
    def setLayerDefaultStyle(self,layer, stylename):
        self.call_api(f"/layers/{layer}.xml",  GSAPIClient.PUT,body=f"<layer><defaultStyle><name>{stylename}</name></defaultStyle></layer>",header_params = {"Content-Type":"text/xml"})
        
    def addLayerStyle(self,layer, stylename, stylefile, defaultStyle = False):
        self.call_api(f"/layers/{layer}/styles",  GSAPIClient.POST,
                      body=f'<?xml version="1.0" encoding="UTF-8"?><StyleInfoPost><name>{stylename}</name><filename>{stylefile}</filename></StyleInfoPost>',
                      header_params = {"Content-Type":"application/xml"},
                      query_params={"default":defaultStyle})


    def setCoverageTemplate(self, data, template,workspace=None, storeName=None,coverage=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/coveragestores/{storeName}"   
            if coverage:
                path +=f"/coverages/{coverage}"   
            
        path +=f"/templates/{template}.ftl"
        print(f"template path {path}")
        res = self.call_api(path, GSAPIClient.PUT,body=data,header_params = {"Content-Type":"text/plain"})
        return res
    
    
    def setFeatureTemplate(self, data, template,workspace=None, storeName=None,feature=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/datastores/{storeName}"   
            if feature:
                path +=f"/featuretypes/{feature}"   
            
        path +=f"/templates/{template}.ftl"   
        res = self.call_api(path, GSAPIClient.PUT,body=data,header_params = {"Content-Type":"text/plain"})
        return res
        
    def getCoverageTemplate(self, template,workspace=None, storeName=None,coverage=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/coveragestores/{storeName}"   
            if coverage:
                path +=f"/coverages/{coverage}"   
            
        path +=f"/templates/{template}.ftl"   
        res = self.call_api(path, GSAPIClient.GET)
        return res
        
    def getFeatureTemplate(self, template,workspace=None, storeName=None,feature=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/datastores/{storeName}"   
            if feature:
                path +=f"/featuretypes/{feature}"   
            
        path +=f"/templates/{template}.ftl"   
        res = self.call_api(path, GSAPIClient.GET)
        return res

    def deletetCoverageTemplate(self, template, workspace=None, storeName=None,coverage=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/coveragestores/{storeName}"   
            if coverage:
                path +=f"/coverages/{coverage}"   
            
        path +=f"/templates/{template}.ftl"   
        res = self.call_api(path, GSAPIClient.DELETE)
        return res
        
    def deleteFeatureTemplate(self, template,workspace=None, storeName=None,feature=None):
        path = ""
        if workspace:
            path +=f"/workspaces/{workspace}"
        if storeName:
            path +=f"/datastores/{storeName}"   
            if feature:
                path +=f"/featuretypes/{feature}"   
            
        path +=f"/templates/{template}.ftl"   
        res = self.call_api(path, GSAPIClient.DELETE)
        return res
    
        
    def getLayerStyles(self,layer,workspace = None):
        if workspace:
            layerdat = self.call_api(f"/workspaces/{workspace}/layers/{layer}/styles", GSAPIClient.GET)
        else:
            layerdat = self.call_api(f"/layers/{layer}/styles", GSAPIClient.GET)
        
        return layerdat
        
    def addStyle(self, stylename, stylefile):
        self.call_api("/styles",  GSAPIClient.POST,
                      body=f'<?xml version="1.0" encoding="UTF-8"?><StyleInfoPost><name>{stylename}</name><filename>{stylefile}</filename></StyleInfoPost>',
                      header_params = {"Content-Type":"application/xml"})
    
    """
    def updateStyle(self,workspaceName,storeName, data):
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}", GSAPIClient.PUT,body=data)
        return stores
    
    def updateStyleGroup(self,workspaceName,storeName, coverage,data, headers = {"Content-Type":"text/xml"}):
        '''
         "Content-Type: text/xml" or
         'Content-Type: application/json'
         
        '''
        stores = self.call_api(f"/workspaces/{workspaceName}/coveragestores/{storeName}/coverages/{coverage}", GSAPIClient.PUT,body=data,header_params=headers)
        return stores
    
    """
    
    
    def buildStyle(self,styleName,  zipdata = None,workspace = None):#, headers = {"Content-Type":"application/zip"}):
        '''
        style can be of json, xml or a zip package
        
        zipdata is binary data already!!!
        
        '''
        
        q = None
        if styleName:
            q = {"name":styleName}
        headers = {"Content-Type":"application/xml"}
        if zipdata :
            if isinstance(zipdata,bytes):
                headers = {"Content-Type":"application/zip"}
                
            elif isinstance(zipdata,str):
                try:                
                    styledata = json.loads(zipdata)
                    headers = {"Content-Type":"application/json"}
                    
                except:
                    # parse xml ....
                    idx = zipdata.find("<StyledLayerDescriptor")
                    if idx >=0:
                        headers = {"Content-Type":"application/vnd.ogc.sld+xml:"}
                        
        
        if workspace:
            stores = self.call_api(f"/workspaces/{workspace}/styles", GSAPIClient.POST,body=zipdata,header_params=headers,query_params=q)
        else:    
            stores = self.call_api(f"/styles", GSAPIClient.POST,body=zipdata,header_params=headers,query_params=q)
        return stores


    def createStyle(self,styleName,  workspace = None):
        if workspace:
            store = self.call_api(f"/workspaces/{workspace}/styles/{styleName}", GSAPIClient.POST)
        else:
            store = self.call_api(f"/styles/{styleName}", GSAPIClient.POST)
        return store
    
    
    
    
    def getHREF(self,specs):
        response = self.__rawclient.get(specs["href"])
        if 200 == response.status_code:
            return response.json()
        print(response.data)
        
        return None
    
    def createWorkspace(self,workspaceName, **kwargs):
        ws = self.call_api(f"/workspaces", GSAPIClient.POST, body={"workspace": {"name": workspaceName}},**kwargs)
        return ws
    
    def testWorkspace(self,workspaceName, **kwargs):
        ws = self.call_api(f"/workspaces/{workspaceName}", GSAPIClient.GET,query_params={"quietOnNotFound":True})
        if ws is None:
            return self.createWorkspace(workspaceName, **kwargs)
        return ws
    
    
    def clearWorkspace(self,ws="tmp"):
        res = self.call_api(f"/workspaces/{ws}", GSAPIClient.DELETE, query_params={"recurse": True})
        return res
    
    
    def getWorkspaces(self, **kwargs):
        ws = self.call_api(f"/workspaces", GSAPIClient.GET)
        return ws
        
class GSAuthClient(GSAPIClient):
        
    def __init__(self,apiconnection):
        
        GSAPIClient.__init__(self, apiconnection)
        self._query_api_key_name = self._apiconnection["auth"]
        self._query_api_key = self._apiconnection["auth-key"]
        
        

        
        
        

    
    def call_api(self, resource_path, method,
             path_params=None, query_params=None, header_params=None,
             body=None, post_params=None, files=None,
             response_type=object, auth_settings=None, async_req=None,
             _return_http_data_only=True, collection_formats=None,
             _preload_content=True, _request_timeout=None, _raise_error= False):
    
        
        if query_params:
            # allow overriding and ensure its not doubling up
            query_params = {**{self._query_api_key_name:self._query_api_key},**query_params}
        else:
            query_params = {self._query_api_key_name:self._query_api_key}
            
        return super().call_api(resource_path, method, path_params, query_params, 
                         header_params, body, post_params, files, response_type, 
                         auth_settings, async_req, _return_http_data_only, 
                         collection_formats, _preload_content, 
                         _request_timeout, _raise_error)
            
class GSOWSClient(GSAPIClient):
        
    def __init__(self,apiconnection,owsconnection):
        self._owsconnection = owsconnection["url"]
        
        # strip this as  its no longer supported, append the GS > 2.23 
        if self._owsconnection.endswith("ows"):
            # ensure slash goes as well
            self._owsconnection = self._owsconnection[:-4]
        elif self._owsconnection.endswith("ows/"):
            self._owsconnection = self._owsconnection[:-5]
            
        GSAPIClient.__init__(self, apiconnection)
        
        
            
    def _printConnection(self):
        logme("OWS {}".format(self._owsconnection))
        super()._printConnection()
        
    def getCapabilities(self, service = "WFS", workspace = None):
        # bypass call_api,,"version":_versionForService(service)
        if workspace:
            restreply = self.rest_client.request(GSAPIClient.GET, "{}/{}/{}".format(self._owsconnection,str(workspace).lower()/service.lower()), {"service":service,"request":"GetCapabilities"})
        else:
            restreply = self.rest_client.request(GSAPIClient.GET, "{}/{}".format(self._owsconnection,service.lower()), {"service":service,"request":"GetCapabilities"})
        if restreply.status == 200:
            return restreply.data

        print("Rest query failed status {} - reason {}, {}".format(restreply.status),restreply.data,restreply.reason)
        return None
    

def createAndPublishFeature(gsclient,ws,store, layer, datafile, ftype = "shp",abstract="", doconfigure= False, srs="EPSG:4326", defaultStyle = None, **kwargs):
    
    gsclient.testWorkspace(ws)
    
    
    storeconfig  = gsclient.getFeatureStore(ws,store)
    if not storeconfig:
        from pathlib import Path
        fnamep = Path(datafile)
        headers = contentType4suffix(".zip")
        ct = contentType4suffix(fnamep.suffix)
        if ct :
            headers = ct
        with fnamep.open('rb') as fp:
            res = gsclient.buildFeatureStoreAndType(ws,store,fp.read(),ftype=ftype, query={"target":ftype,"configure":"all" if doconfigure else None,"filename":layer+f".{ftype}"},headers=headers)
            print(res)
        storeconfig  = gsclient.getFeatureStore(ws,store)
    if  storeconfig is None:
        raise ValueError("creating Feature Store failed")
    
    logme(storeconfig)
    #{'dataStore': {'name': 'densityt36', 'type': 'Shapefile', 'enabled': True, 'workspace': {'name': 'tmp', 'href': 'http://localhost:9908/geoserver/rest/workspaces/tmp.json?npp-auth=364c9181-6e30-4cb6-b1ab-e67177a5024c'}, 'connectionParameters': {'entry': [{'@key': 'namespace', '$': 'tmp'}, {'@key': 'url', '$': 'file:/geoserver/data/npp/data/tmp/densityt36/'}]}, '_default': False, 'dateCreated': '2025-03-26 05:57:47.189 UTC', 'disableOnConnFailure': False, 'featureTypes': 'http://localhost:9908/geoserver/rest/workspaces/tmp/datastores/densityt36/featuretypes.json?npp-auth=364c9181-6e30-4cb6-b1ab-e67177a5024c'}}

    storeconfig = storeconfig["dataStore"]
    if "featureTypes" in storeconfig:
        fetauretypes =  gsclient.getHREF({"href":storeconfig["featureTypes"]})
        if isinstance(fetauretypes["featureTypes"], dict) and len(fetauretypes["featureTypes"]["featureType"]) > 0:
            layer = fetauretypes["featureTypes"]["featureType"][0]["name"]
        
            testlayer = gsclient.getFeatureType(ws,store,layer)
            testlayer = gsclient.getFeatureType(ws,store,quote(layer))
            
        else:
        
        
            workspace = storeconfig["workspace"]
            wsurl = workspace["href"]
            enindex = wsurl.find(".json")
            wsindex = wsurl.find("workspace")
            wsstart = wsurl[:enindex]
            wsend = wsurl[enindex:]
            resstart = wsurl[:wsindex]
            
            featuretypeinfo = deepcopy(feturetypeinfo_template)
            featuretypeinfo["name"] =  layer
            featuretypeinfo["nativeName"] = layer
            featuretypeinfo["title"] = layer
            featuretypeinfo["store"] = {
                        "@class": "dataStore",
                        "name": "{}:{}".format(storeconfig["workspace"]["name"],storeconfig["name"]),
                        "href": wsurl
                    }
            featuretypeinfo["namespace"]["name"] = ws
            featuretypeinfo["latLonBoundingBox"]=bbox_dummy
            featuretypeinfo["nativeBoundingBox"]=bbox_dummy
            featuretypeinfo["srs"] = bbox_dummy["crs"]
            featuretypeinfo["projectionPolicy"] = "FORCE_DECLARED" 
            
            templateFeatureType ={"featureType": {"name": layer,
                                                  
                    "nativeName": layer,
                     "abstract":abstract,
                    "title": layer,
                    "keywords": {
                        "string": [
                            "features",
                            layer
                        ]
                    },
                    "srs": srs}
            }
            

            
            templateFeatureType["featureType"]["namespace"] = {
                        "name": ws,
                        "href": f"{resstart}namespaces/{ws}{wsend}"
                    }
            
            templateFeatureType["featureType"]["store"] = {
                        "@class": "dataStore",
                        "name": "{}:{}".format(storeconfig["workspace"]["name"],storeconfig["name"]),
                        "href": wsurl
                    }
            
            templateFeatureType["featureType"]["attributes"]={"attribute":[]}
            
            res = gsclient.createFeatureTypeOnDatastore(ws,store,{"featureType":featuretypeinfo})#,**{"header_params": {"Content-Type":"application/json"}})
        
            #res = gsclient.updateFeatureType(ws,store,layer,templateFeatureType, **{"query_params":{"recalculate":"nativebbox,latlonbbox"}})#,**{"header_params": {"Content-Type":"application/json"}})
    
    
            logme(res)
    
    
    if defaultStyle:
        gsclient.setLayerDefaultStyle(quote(layer),defaultStyle)
        
    return ws,store, layer


def createAndPublishCoverage(gsclient,ws,store, layer, datafile, rasterType = "geotiff",abstract="",  defaultStyle = 'None', **kwargs):

    gsclient.testWorkspace(ws)
    
    
    storeconfig  = gsclient.getCoverageStore(ws,store)
    if not storeconfig:
        from pathlib import Path
        fnamep = Path(datafile)
        with fnamep.open('rb') as fp:
            res = gsclient.buildCoverageStoreAndType(ws,store,fp.read(),rasterType=rasterType)
            print(res)
        storeconfig  = gsclient.getFeatureStore(ws,store)
        if  storeconfig is None:
            raise ValueError("creating Feature Store failed")
        
    
    if defaultStyle:
        gsclient.setLayerDefaultStyle(quote(layer),defaultStyle)
        
    return ws,store, layer
    
def createAndPublishCOG(gsclient,ws,store, layer, url, abstract="", defaultStyle = None, **kwargs):
    
    gsclient.testWorkspace(ws)
    
    storedef = {
    "coverageStore": {
        "name": store,
        "type": "GeoTIFF",
        "enabled": True,
        "workspace": {
            "name": ws
        },
        "metadata": {
            "entry": {        
                "@key": "CogSettings.Key",
                "cogSettings": {
                    "useCachingStream": False,
                    "rangeReaderSettings": "HTTP"
                }
            }
        },
        "_default": False,
        "disableOnConnFailure": False,
        "url": f"cog://{url}"    }}

    
    res = gsclient.createCoverageStore(ws, storedef)
    logme(res)
    
    
    layerdef = {"coverage": {
        "name": layer,
        "abstract":abstract,
        "srs": "EPSG:4326",
        "enabled": True,
    
        "nativeFormat": "GeoTIFF"
    
        }}
    if kwargs and "coverage" in kwargs:
        # we force local as that is what we are here for, making a COG raster
        layerdef = {"coverage":{**layerdef["coverage"],**kwargs["coverage"],"nativeFormat": "GeoTIFF","name": layer}}
        
    res = gsclient.createCoverage(ws,store, layerdef)
    logme(res)
    
    
    if defaultStyle:
        gsclient.setLayerDefaultStyle(layer,defaultStyle)
    
    
def createCOGImageStore(gsclient,tempdir, workspaceName,storeName, imagelist,baseurl, timepattern='[0-9]{8}'):
    '''
    not working as expected ....
    
    '''
    
    from pathlib import Path
    import os
    tmppdir = Path(tempdir)
    
    tmppdir.mkdir(parents=True, exist_ok=True)
    

    
    
    with tmppdir.joinpath("indexer.properties").open('w') as fp:
        fp.write('Cog=true\n')
        fp.write('PropertyCollectors=TimestampFileNameExtractorSPI[timeregex](time)\n')
        fp.write('Schema=*the_geom:Polygon,location:String,time:java.util.Date\n')
        fp.write('CanBeEmpty=true\n')
        fp.write(f'Name={storeName}\n')
        
    # or timepattern
    with tmppdir.joinpath("timeregex.properties").open('w') as fp:
        fp.write(f'regex={timepattern}\n')
    
    zipfile_name = str(tmppdir.joinpath(storeName.replace(' ','')+".zip"))
    import zipfile
    zip = zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED)
    cwd = os.getcwd()
    os.chdir(str(tmppdir))
    zip.write("indexer.properties")
    zip.write("timeregex.properties")
    zip.close()
    os.chdir(cwd)
    
    
    with open(zipfile_name,"rb") as fp:
        zipdata= fp.read()
    
    # ignore if exists
    res = gsclient.createWorkspace(workspaceName)
    logme(res)
    
    
    res = gsclient.buildCoverageStoreAndType(workspaceName,storeName,"imagemosaic", zipdata ,params={"configure":"none"})
    print(res)
    
    res = gsclient.createCoverageProtoypeRemote(workspaceName,storeName,ensureURLPath(baseurl,imagelist[0]))
    logme(res)
    

    res = gsclient.updateCoverage(workspaceName,storeName,f'''<coverage><name>{storeName}</name>
  <nativeName>{storeName}</nativeName>
  <enabled>true</enabled>
  <metadata>
    <entry key="time">
      <dimensionInfo>
        <enabled>true</enabled>
        <presentation>LIST</presentation>
        <units>ISO8601</units>
        <defaultValue>
          <strategy>MAXIMUM</strategy>
        </defaultValue>
      </dimensionInfo>
    </entry>
  </metadata>
</coverage>''')
    logme(res)
        
    # add the rest of the references, we should have at least 2 ...
    for i in range(1,len(imagelist)):
        res = gsclient.createCoverageProtoypeRemote(workspaceName,storeName,ensureURLPath(baseurl,imagelist[i]))
        logme(res)
    
    
        
    
    
    
    
    
def __specsForProtocol(protocol):
    p = protocol.lower()
    
    if p == "wms":
        return {"request":"GetMap",
                 "layer":"layers",
                 "protocol":"WMS",
                 "version":"1.1.0.",
                 "more":{"srs":"EPSG:4326",
                         "WIDTH":768,"HEIGHT":512,
                         "format":"image/png"}
                }
    
    elif p == "wfs":
        return  {"request":"GetFeature",
                 "protocol":"WFS",
                 "layer":"typeNames",
                 "more":{"outputFormat":"application/json"},
                 "version":"2.0.0"}
        
    elif p =="csv":
        return  {"request":"GetFeature",
                 "protocol":"WFS",
                 "layer":"typeNames",
                 "more":{"outputFormat":"text/csv"},
                 "version":"2.0.0"}
        

def buildLayer(owsurl, protocol, layer,extents =None):
    from urllib.parse import quote_plus
    owsurl = validateOWSURL(owsurl,protocol)
    
    specs = __specsForProtocol(protocol)
    protocol = specs["protocol"]
    request = specs["request"]
    version = specs["version"]
    layerdef = specs["layer"]
    layer = quote_plus(layer)
    morelist = []
    if extents and 'bbox' in extents:
        if isinstance(extents['bbox'],(list,tuple)):
            mv = quote_plus(",".join( [str(c) for c in extents['bbox']]))
        else:# isinstance(extents['bbox'],str):
            mv = mv = quote_plus(extents['bbox'])
            
        morelist.append(f"bbox={mv}")
        
    for m in specs["more"]:
        mv = quote_plus(str(specs["more"][m]))
        morelist.append(f"{m}={mv}")
        
    more = ""
    if morelist:
        more="&"
        more += "&".join(morelist)
    
    qstring = f"service={protocol}&version={version}&{layerdef}={layer}&request={request}{more}"
    return f"{owsurl}?{qstring}"


            
    