pyrest
============

Python base for REST API

A simple generic REST APIClient that takes care of the encoding and packaging of parameters.
It modeled after the swagger REST client and does also support pydantic models if defined in subclasses.

# Usage


This package is a library to be build on, if not use call to cal_api(...)

It provides to entry points:
build a REST API client simply by extending  the APIClient and map path to function without the need of decorators.


build a REST Server without the need of setting up protocols and server components, simply provide a single callable which gets handed a subset of path operations. Alternatively replace the Routable object under FastAPI to implement more complex behaviour.
Needless to say that what ever delegate wants to be instantiated, it needs to be available/in the path. 

To extend the docker image, tag and build ontop with your handler code, provide handler config as in pyrest/echo.json

	
Dependencies - rest client
==========================

* six
* certifi


Dependencies - rest server
==========================

* typing_extensions
* pydantic
* uvicorn
* starlette
* anyio
* fastapi
* classy_fastapi
* h11
* click 
* sniffio
* python-multipart


License
=======

Short version: [MIT](https://en.wikipedia.org/wiki/MIT_License)
Long version: see [LICENSE](LICENSE) file

_____
Blurb
=====

this collection came about because i need to do the same thing over and over again and needed a quick fix for the boiler plate code.
	 