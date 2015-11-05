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
__version__    = "1.0"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

import json
import ConfigParser

# GridEngine API Server configuration
class geapiserver_cfg:
    geConfig = {}

    def __init__(self,configFile):
        config = ConfigParser.ConfigParser()
        config.read(configFile)
        # geapiserver
        self.geConfig['geapiver'          ] = config.get('geapiserver','geapiver')
        self.geConfig['geapiserver_name'  ] = "%s %s" % (config.get('geapiserver','geapiserver_name')
				                                      ,self.geConfig['geapiver'])
        self.geConfig['geapisrv_host'     ] = config.get('geapiserver','geapisrv_host')
        self.geConfig['geapisrv_port'     ] = config.get('geapiserver','geapisrv_port')
        self.geConfig['geapisrv_iosandbox'] = config.get('geapiserver','geapisrv_iosandbox')
        self.geConfig['geapisrv_geappid'  ] = config.get('geapiserver','geapisrv_geappid')

        # geapiserver_db
        self.geConfig['geapisrv_db_host'] = config.get('geapiserver_db','geapisrv_db_host')
        self.geConfig['geapisrv_db_port'] = config.get('geapiserver_db','geapisrv_db_port')
        self.geConfig['geapisrv_db_user'] = config.get('geapiserver_db','geapisrv_db_user')
        self.geConfig['geapisrv_db_pass'] = config.get('geapiserver_db','geapisrv_db_pass')
        self.geConfig['geapisrv_db_name'] = config.get('geapiserver_db','geapisrv_db_name')
        self.showConf()

    def showConf(self):
        config = ("GridEngine API Server config\n"
               "-----------------------------\n"
			   "%s\n" % json.dumps(self.geConfig, indent=4))
        print config

    def getConfValue(self,key):
        def_value = None
        if   key == 'geapiver'          : def_value = 'v.10'
        elif key == 'geapiserver_name'  : def_value = 'GridEngine API Server % s' % self.getConfValue('geapiver')
        elif key == 'geapisrv_host'     : def_value = 'localhost'
        elif key == 'geapisrv_port'     : def_value = '7777'
        elif key == 'geapisrv_db_host'  : def_value = 'localhost'
        elif key == 'geapisrv_db_port'  : def_value = '3306'
        elif key == 'geapisrv_db_user'  : def_value = 'localhost'
        elif key == 'geapisrv_db_pass'  : def_value = 'geapiserver_password'
        elif key == 'geapisrv_db_name'  : def_value = 'geapiserver'
        elif key == 'geapisrv_iosandbox': def_value = '/tmp'
        elif key == 'geapisrv_geappid'  : def_value = '10000'
        elif key == 'gejson_indent'     : def_value = '4'
        else:
			print "[WARNING] Not found default value for key: '%s'" % key
        return self.geConfig.get(key,def_value)

