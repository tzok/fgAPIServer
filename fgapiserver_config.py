#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import yaml
import logging
import logging.config

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-10-18 14:17:10'

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.yaml'

# Logging object
logger = logging.getLogger(__name__)


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
    def_api_ver = 'v1.0'
    def_fg_ver = __version__

    # Default values; used when conf file does not exists
    # or an option is missing on configuration file
    # the use of default values is notified by the
    # class variable fgConfigMsg
    defaults = {
        'fgapiserver': {
            'fgapiver': def_api_ver,
            'fgapiserver_name': ('FutureGateway API Server % s'
                                 % def_fg_ver),
            'fgapisrv_host': 'localhost',
            'fgapisrv_port': '8888',
            'fgapisrv_debug': 'True',
            'fgapisrv_iosandbox': '/tmp',
            'fgjson_indent': '4',
            'fgapisrv_key': '',
            'fgapisrv_crt': '',
            'fgapisrv_logcfg': 'fgapiserver_log.conf',
            'fgapisrv_dbver': '0.0.13',
            'fgapisrv_secret': '0123456789ABCDEF',
            'fgapisrv_notoken': 'False',
            'fgapisrv_notokenusr': 'futuregateway',
            'fgapisrv_lnkptvflag': 'False',
            'fgapisrv_ptvendpoint': 'http://localhost/ptv',
            'fgapisrv_ptvuser': 'ptvuser',
            'fgapisrv_ptvpass': 'ptvpass',
            'fgapisrv_ptvdefusr': 'futuregateway',
            'fgapisrv_ptvdefgrp': 'administrator',
            'fgapisrv_ptvmapfile': 'fgapiserver_ptvmap.json',
            'dbcon_retry_times': '-1',
            'dbcon_retry_delay': '5'},
        'fgapiserver_db': {
            'fgapisrv_db_host': 'localhost',
            'fgapisrv_db_port': '3306',
            'fgapisrv_db_user': 'fgapiserver',
            'fgapisrv_db_pass': 'fgapiserver_password',
            'fgapisrv_db_name': 'fgapiserver'},
        'gridengine_ei': {
            'utdb_host': 'localhost',
            'utdb_port': '3306',
            'utdb_user': 'tracking_user',
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
                 'utdb_port',
                 'dbcon_retry_times',
                 'dbcon_retry_delay']
    bool_types = ['fgapisrv_lnkptvflag',
                  'fgapisrv_notoken',
                  'fgapisrv_debug']

    # Configuration messages informs about the loading
    # of configuration values
    fg_config_messages = "Configuration messages ...\n"

    def __init__(self, config_file):
        """
        Initialize the configutation object loading the given
        configuration file
        """
        dict.__init__(self)

        # Load config from config_file
        if config_file is None:
            config_file = ''
        conf_yaml = {}
        try:
            conf_file = open(config_file, 'r')
            conf_yaml = yaml.safe_load(conf_file)
            self.config_file = config_file
        except IOError:
            logging.warning(
                "Couldn't find configuration file '%s'; "
                " default options will be used\n" % config_file)
            pass

        # Load configuration
        for section in self.defaults.keys():
            for conf_name in self.defaults[section].keys():
                def_value = self.defaults[section][conf_name]
                try:
                    self[conf_name] = conf_yaml[section][conf_name]
                except KeyError:
                    self[conf_name] = def_value
                    self.fg_config_messages +=\
                        ("[WARNING]:Couldn't find option '%s' "
                         "in section '%s'; "
                         "using default value '%s'\n"
                         % (conf_name, section, def_value))
                # The use of environment varialbes override any default or
                # configuration setting present in the configuration file
                try:
                    env_value = os.environ[conf_name.upper()]
                    # environ may return "''" for some variables
                    if env_value[-1:] == "'" and env_value[0:1] == "'":
                        env_value = env_value[1:-1]
                    self.fg_config_messages += \
                        ("Environment bypass of '%s': '%s' <- '%s'\n" %
                         (conf_name, self[conf_name], env_value))
                    self[conf_name] = env_value
                except KeyError:
                    # Corresponding environment variable not exists
                    pass

        # Show configuration in Msg variable
        if self['fgapisrv_debug']:
            logging.debug(self.show_conf())

    def __getitem__(self, key):
        conf_value = dict.__getitem__(self, key)
        if key in self.bool_types:
            conf_value = (str(conf_value).lower() == 'true')
        elif key in self.int_types:
            conf_value = int(conf_value)
        if conf_value is None:
            conf_value = ''
        return conf_value

    def __setitem__(self, key, value):
        if key in self.bool_types:
            conf_value = (str(value).lower() == 'true')
        elif key in self.int_types:
            conf_value = int(value)
        else:
            conf_value = value
        dict.__setitem__(self, key, conf_value)

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

    def __str__(self):
        """
        Perfor object string representation equals to representation
        :return:
        """
        return self.__repr__()

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
        return self.fg_config_messages

    def load_config(self, cfg_dict):
        """
        Save configuration settings stored in the given dictionary
        """
        if cfg_dict is not None:
            for key in cfg_dict:
                value = cfg_dict[key]
                self[key] = value


# FutureGateway configuration instance
fg_config = FGApiServerConfig(fgapiserver_config_file)
