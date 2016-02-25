#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
# Consorzio COMETA (COMETA), Italy
#
# See http://www.infn.it and and http://www.consorzio-cometa.it for details on
# the copyright holders.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
__author__     = "Riccardo Bruno"
__copyright__  = "2015"
__license__    = "Apache"
__version__    = "v0.0.1-12-ge204c62-e204c62-16"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

import json
import ConfigParser

# GridEngine API Server configuration
class fgapiserver_cfg:
    fgConfig = {}

    def __init__(self,configFile):
        config = ConfigParser.ConfigParser()
        config.read(configFile)
        # fgapiserver
        self.fgConfig['fgapiver'          ] = config.get('fgapiserver','fgapiver')
        self.fgConfig['fgapiserver_name'  ] = "%s %s" % (config.get('fgapiserver','fgapiserver_name')
				                                      ,self.fgConfig['fgapiver'])
        self.fgConfig['fgapisrv_host'     ] = config.get('fgapiserver','fgapisrv_host')
        self.fgConfig['fgapisrv_port'     ] = config.get('fgapiserver','fgapisrv_port')
        self.fgConfig['fgapisrv_debug'    ] = config.get('fgapiserver','fgapisrv_debug')
        self.fgConfig['fgapisrv_iosandbox'] = config.get('fgapiserver','fgapisrv_iosandbox')
        self.fgConfig['fgapisrv_geappid'  ] = config.get('fgapiserver','fgapisrv_geappid')
        self.fgConfig['fgapisrv_key'      ] = config.get('fgapiserver','fgapisrv_key')
        self.fgConfig['fgapisrv_crt'      ] = config.get('fgapiserver','fgapisrv_crt')

        # fgapiserver_db
        self.fgConfig['fgapisrv_db_host'] = config.get('fgapiserver_db','fgapisrv_db_host')
        self.fgConfig['fgapisrv_db_port'] = config.get('fgapiserver_db','fgapisrv_db_port')
        self.fgConfig['fgapisrv_db_user'] = config.get('fgapiserver_db','fgapisrv_db_user')
        self.fgConfig['fgapisrv_db_pass'] = config.get('fgapiserver_db','fgapisrv_db_pass')
        self.fgConfig['fgapisrv_db_name'] = config.get('fgapiserver_db','fgapisrv_db_name')
        self.showConf()

    def showConf(self):
        config = ("FutureGateway API Server config\n"
               "----------------------------------\n"
			   "%s\n" % json.dumps(self.fgConfig, indent=4))
        print config

    def getConfValue(self,key):
        def_value = None
        if   key == 'fgapiver'          : def_value = 'v.10'
        elif key == 'fgapiserver_name'  : def_value = 'GridEngine API Server % s' % self.getConfValue('fgapiver')
        elif key == 'fgapisrv_host'     : def_value = 'localhost'
        elif key == 'fgapisrv_port'     : def_value = '8888'
        elif key == 'fgapisrv_debug'    : def_value = 'True'
        elif key == 'fgapisrv_db_host'  : def_value = 'localhost'
        elif key == 'fgapisrv_db_port'  : def_value = '3306'
        elif key == 'fgapisrv_db_user'  : def_value = 'localhost'
        elif key == 'fgapisrv_db_pass'  : def_value = 'fgapiserver_password'
        elif key == 'fgapisrv_db_name'  : def_value = 'fgapiserver'
        elif key == 'fgapisrv_iosandbox': def_value = '/tmp'
        elif key == 'fgapisrv_geappid'  : def_value = '10000'
        elif key == 'fgjson_indent'     : def_value = '4'
        elif key == 'fgapisrv_key'      : def_value = ''
        elif key == 'fgapisrv_crt'      : def_value = ''
        else:
			print "[WARNING] Not found default value for key: '%s'" % key
        return self.fgConfig.get(key,def_value)

