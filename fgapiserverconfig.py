#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
#
# See http://www.infn.it  for details on the copyrigh holder
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

import os
import sys
import json
import ConfigParser

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.7-1"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


# GridEngine API Server configuration


class FGApiServerConfig(dict):
    """
    FutureGateway API Server configuration values class
    
    This class inherits from dict class aiming to store all configutation
    values of the FutureGateway module fgAPIServer.  The class internally
    stores all available configuration settings and their related default
    values. The class also takes configuration values from environment
    variables, in this case they have the higher priority
    """

    # Configuration file
    config_file = None

    # Default values for configuration settings  
    def_api_ver = '1.0'
    def_fg_ver = __version__

    # Default values; used when conf file does not exists
    # or an option is missing on configuration file
    # the use of default values is notified by the
    # class variable fgConfigMsg
    defaults = {
        'fgapiserver': {
            'fgapiver': def_api_ver,
            'fgapiserver_name': ('GridEngine API Server % s'
                                 % def_fg_ver),
            'fgapisrv_host': 'localhost',
            'fgapisrv_port': '8888',
            'fgapisrv_debug': 'True',
            'fgapisrv_iosandbox': '/tmp',
            'fgjson_indent': '4',
            'fgapisrv_key': '',
            'fgapisrv_crt': '',
            'fgapisrv_logcfg': 'fgapiserver_log.conf',
            'fgapisrv_dbver': '',
            'fgapisrv_secret': '0123456789ABCDEF',
            'fgapisrv_notoken': 'False',
            'fgapisrv_notokenusr': 'futuregateway',
            'fgapisrv_lnkptvflag': 'False',
            'fgapisrv_ptvendpoint': 'http://localhost/ptv',
            'fgapisrv_ptvuser': 'ptvuser',
            'fgapisrv_ptvpass': 'ptvpass',
            'fgapisrv_ptvdefusr': 'futuregateway',
            'fgapisrv_ptvdefgrp': 'administrator',
            'fgapisrv_ptvmapfile': 'fgapiserver_ptvmap.json'},
        'fgapiserver_db': {
            'fgapisrv_db_host': 'localhost',
            'fgapisrv_db_port': '3306',
            'fgapisrv_db_user': 'localhost',
            'fgapisrv_db_pass': 'fgapiserver_password',
            'fgapisrv_db_name': 'fgapiserver'},
        'gridengine_ei': {
            'utdb_host': 'localhost',
            'utdb_port': '3306',
            'utdb_user': 'localhost',
            'utdb_pass': 'fgapiserver_password',
            'utdb_name': 'fgapiserver',
            'fgapisrv_geappid': '10000'} 
    }

    # Configuration data types
    # Following vectors consider only int and bool types remaining
    # configuration options will be considered strings as default
    int_types = ['fgjson_indent',
                 'fgapisrv_geappid',
                 'fgapisrv_port',
                 'fgapisrv_db_port',
                 'utdb_port']
    bool_types = ['fgapisrv_lnkptvflag',
                  'fgapisrv_notoken',
                  'fgapisrv_debug']

    # Configuration messages informs about the loading
    # of configuration values
    fgConfigMsg = "Configuration messages ...\n"

    def __init__(self, config_file):
        """
        Initialize the configutation object loading the given
        configuration file
        """
        dict.__init__(self)

        # Parse configuration file
        config = ConfigParser.ConfigParser()
        if config_file is None \
                or len(config.read(config_file)) == 0:
            self.fgConfigMsg += (
                    "[WARNING]: Couldn't find configuration file '%s'; "
                    " default options will be uses\n" % config_file)
        else:
            # Store configuration file name
            self.config_file = config_file

        # Load configuration
        for section in self.defaults.keys():
            for conf_name in self.defaults[section].keys():
                def_value = self.defaults[section][conf_name]
                try:
                    self[conf_name] = config.get(section, conf_name)
                except ConfigParser.Error:
                    self[conf_name] = def_value
                    self.fgConfigMsg += ("[WARNING]:Couldn't find option '%s' "
                                         "in section '%s'; "
                                         "using default value '%s'"
                                         % (conf_name, section, def_value))
                # The use of environment varialbes override any default or
                # configuration setting present in the configuration file
                try:
                    env_value = os.environ[conf_name.upper()]
                    self.fgConfigMsg += \
                        ("Environment bypass of '%s': '%s' <- '%s'\n" %
                         (conf_name, self[conf_name], env_value))
                    self[conf_name] = env_value
                except KeyError:
                    pass
        # Show configuration in Msg variable
        if self['fgapisrv_debug']:
            self.fgConfigMsg += self.show_conf()

    def __getitem__(self, key):
        conf_value = dict.__getitem__(self, key)
 
        if key in self.bool_types: 
            conf_value = (str(conf_value).lower() == 'true')
        if key in self.int_types:
            conf_value = int(conf_value)
        
        return conf_value

    def __repr__(self):
        """
        Perform object representation as in defaults scheme
        :return:
        """
        config = {}
        for section in self.defaults.keys():
            section_config = {}
            for key in self.defaults[section]:
                section_config[key] = self[key]
            config[section] = section_config
        return json.dumps(config, indent=int(self['fgjson_indent']))

    def show_conf(self):
        """
        Show the loaded APIServer fron-end configuration
        :return:
        """
        config = {}
        for section in self.defaults.keys():
            section_config = {} 
            for key in self.defaults[section]:
                section_config[key] = self[key]
            config[section] = section_config

        return ("---------------------------------\n"
                " FutureGateway API Server config \n"
                "---------------------------------\n"
                "%s\n" % self)

    def get_messages(self):
        """
        Return the messages created during configuration loading
        """
        return self.fgConfigMsg

    def load_config(self, cfg_dict):
        """
        Save configuration settings stored in the given dictionary
        """
        if cfg_dict is not None:
            for key in cfg_dict:
                value = cfg_dict[key]
                self[key] = value
