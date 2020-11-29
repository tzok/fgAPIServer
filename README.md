# FutureGateway API Server front-end (fgAPIServer)
[![Travis](https://travis-ci.org/FutureGatewayFramework/fgAPIServer.svg?branch=EnvConfig)](https://travis-ci.org/FutureGatewayFramework/fgAPIServer)
[![License](https://img.shields.io/github/license/FutureGateway/geAPIServer.svg?style?flat)](http://www.apache.org/licenses/LICENSE-2.0.txt)

This project implements the interface of a RESTful API Server, compliant with [CSGF APIs][specs] specifications. Any activity processed by this interface will be then processed by the [API Server Daemon][APIServerDaemon] component.
The principal aim of this component is to accept incoming REST APIs, verify user rights and provide back a result. Some APIs require to fill a queue table which will be processed by the APIServerDaemon component. 

   [specs]: <http://docs.csgfapis.apiary.io/#reference/v1.0/application/create-a-task>
   [CSGF]: <https://www.catania-science-gateways.it>
   [API Server Daemon]: <https://github.com/FutureGateway/APIServerDaemon>
   
This work is co-funded by the [EOSC-hub project](http://eosc-hub.eu/) (Horizon 2020) under Grant number 777536.
<img src="https://wiki.eosc-hub.eu/download/attachments/1867786/eu%20logo.jpeg?version=1&modificationDate=1459256840098&api=v2" height="24">
<img src="https://wiki.eosc-hub.eu/download/attachments/18973612/eosc-hub-web.png?version=1&modificationDate=1516099993132&api=v2" height="24">
