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

import unittest
import hashlib
import os
from fgapiserver_config import FGApiServerConfig

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


class TestfgAPIServerConfig(unittest.TestCase):

    def setUp(self):
        pass

    @staticmethod
    def banner(test_name):
        print ""
        print "------------------------------------------------"
        print " Testing: %s" % test_name
        print "------------------------------------------------"

    @staticmethod
    def md5sum(filename, blocksize=65536):
        hash_value = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash_value.update(block)
        return hash_value.hexdigest()

    @staticmethod
    def md5sum_str(string):
        return hashlib.md5(string).hexdigest()

    #
    # fgapiserverconfig
    #

    def test_Defaults(self):
        """
        Test default configuration settings using invalid file as class param
        :return:
        """
        self.banner("Defaults config")
        cfg = FGApiServerConfig('')
        print "Configuration: %s" % cfg
        for key in cfg.keys():
            for sec in cfg.defaults.keys():
                for def_key in cfg.defaults[sec]:
                    if key == def_key:
                        print ("cfg['%s'] = '%s' <-> "
                               "cfg.defaults['%s']['%s'] = '%s'") \
                              % (key, cfg[key], sec, def_key,
                                 cfg.defaults[sec][def_key])
                        if not (key in cfg.int_types or
                                key in cfg.bool_types):
                            # fgapisrv_notokenusr param is 'test' for Tests
                            if key == 'fgapisrv_notokenusr':
                                cfg.defaults[sec][def_key] = 'test'
                            self.assertEqual(cfg[key],
                                             cfg.defaults[sec][def_key])
                            break
                        elif key in cfg.int_types:
                            self.assertEqual(cfg[key],
                                             int(cfg.defaults[sec][def_key]))
                            break
                        elif key in cfg.bool_types:
                            # fgapisrv_notoken param is ever TRUE for Tests
                            if key == 'fgapisrv_notoken':
                                cfg.defaults[sec][def_key] = 'True'
                            self.assertEqual(
                                cfg[key],
                                cfg.defaults[sec][def_key].lower() == 'true')
                            break
                        else:
                            print "Unexpected type: '%s' for parameter: '%s'"\
                                  % (type(cfg[key]), key)
                            self.assertEqual(0, 1)
                        print "Reached end while scanning keys"
                        self.assertEqual(0, 1)

    def test_NoneConfigFile(self):
        """
        Test default configuration settings using None as class param
        :return:
        """
        self.banner("None Config")
        cfg = FGApiServerConfig(None)
        for key in cfg.keys():
            for sec in cfg.defaults.keys():
                for def_key in cfg.defaults[sec]:
                    if key == def_key:
                        print ("cfg['%s'] = '%s' <-> "
                               "cfg.defaults['%s']['%s'] = '%s'")\
                              % (key, cfg[key], sec, def_key,
                                 cfg.defaults[sec][def_key])
                        if not (key in cfg.int_types or
                                key in cfg.bool_types):
                            # fgapisrv_notokenusr param is 'test' for Tests
                            if key == 'fgapisrv_notokenusr':
                                cfg.defaults[sec][def_key] = 'test'
                            self.assertEqual(cfg[key],
                                             cfg.defaults[sec][def_key])
                            break
                        elif key in cfg.int_types:
                            self.assertEqual(cfg[key],
                                             int(cfg.defaults[sec][def_key]))
                            break
                        elif key in cfg.bool_types:
                            # fgapisrv_notoken param is ever TRUE for Tests
                            if key == 'fgapisrv_notoken':
                                cfg.defaults[sec][def_key] = 'True'
                            self.assertEqual(
                                cfg[key],
                                cfg.defaults[sec][def_key].lower() == 'true')
                            break
                        else:
                            print "Unexpected type: '%s' for parameter: '%s'"\
                                  % (type(cfg[key]), key)
                            self.assertEqual(0, 1)
                        print "Reached end while scanning keys"
                        self.assertEqual(0, 1)

    def test_DefConfigFile(self):
        """
        Test default configuration settings from configuration file,
        values have to match with defaults
        :return:
        """
        self.banner("Default configuration file")
        cfg = FGApiServerConfig('fgapiserver.conf')
        for key in cfg.keys():
            for sec in cfg.defaults.keys():
                for def_key in cfg.defaults[sec]:
                    if key == def_key:
                        print ("cfg['%s'] = '%s' <-> "
                               "cfg.defaults['%s']['%s'] = '%s'") \
                              % (key, cfg[key], sec, def_key,
                                 cfg.defaults[sec][def_key])
                        if not (key in cfg.int_types or
                                key in cfg.bool_types):
                            # fgapisrv_notokenusr param is 'test' for Tests
                            if key == 'fgapisrv_notokenusr':
                                cfg.defaults[sec][def_key] = 'test'
                            self.assertEqual(cfg[key],
                                             cfg.defaults[sec][def_key])
                            break
                        elif key in cfg.int_types:
                            self.assertEqual(cfg[key],
                                             int(cfg.defaults[sec][def_key]))
                            break
                        elif key in cfg.bool_types:
                            # fgapisrv_notoken param is ever TRUE for Tests
                            if key == 'fgapisrv_notoken':
                                cfg.defaults[sec][def_key] = 'True'
                            self.assertEqual(
                                cfg[key],
                                cfg.defaults[sec][def_key].lower() == 'true')
                            break
                        else:
                            print "Unexpected type: '%s' for parameter: '%s'" \
                                  % (type(cfg[key]), key)
                            self.assertEqual(0, 1)
                        print "Reached end while scanning keys"
                        self.assertEqual(0, 1)

    def test_BothConfig(self):
        """
        Test that both class defaults and file config settings are matching
        :return:
        """
        self.banner("Both config are matching")
        cfg_class = FGApiServerConfig('')
        cfg_file = FGApiServerConfig('fgapiserver.conf')
        print "Class Configuration: %s" % cfg_class
        print "MD5_class: '%s': " % self.md5sum_str("%s" % cfg_class)
        print "File Configuration: %s" % cfg_file
        print "MD5_file:  '%s': " % self.md5sum_str("%s" % cfg_file)
        self.assertEqual(self.md5sum_str("%s" % cfg_class),
                         self.md5sum_str("%s" % cfg_file))

    def test_ConfigDict(self):
        """
        Test that both class defaults and file config settings are matching
        :return:
        """
        self.banner("Config dictionary check")
        cfg = FGApiServerConfig('fgapiserver.conf')
        self.assertEqual("%s" % cfg['fgapiver'], '1.0')
        self.assertEqual("%s" % cfg['fgapiserver_name'],
                         'GridEngine API Server v0.0.7-1')
        self.assertEqual("%s" % cfg['fgapisrv_host'], 'localhost')
        self.assertEqual("%s" % cfg['fgapisrv_port'], '8888')
        self.assertEqual("%s" % cfg['fgapisrv_debug'], 'True')
        self.assertEqual("%s" % cfg['fgapisrv_iosandbox'], '/tmp')
        self.assertEqual("%s" % cfg['fgjson_indent'], '4')
        self.assertEqual("%s" % cfg['fgapisrv_key'], '')
        self.assertEqual("%s" % cfg['fgapisrv_crt'], '')
        self.assertEqual("%s" % cfg['fgapisrv_logcfg'], 'fgapiserver_log.conf')
        self.assertEqual("%s" % cfg['fgapisrv_dbver'], '')
        self.assertEqual("%s" % cfg['fgapisrv_secret'], '0123456789ABCDEF')
        # fgapisrv_notoken is ever True in tests
        self.assertEqual("%s" % cfg['fgapisrv_notoken'], 'True')
        # fgapisrv_notokenusr is ever 'test' in tests
        self.assertEqual("%s" % cfg['fgapisrv_notokenusr'], 'test')
        self.assertEqual("%s" % cfg['fgapisrv_lnkptvflag'], 'False')
        self.assertEqual("%s" % cfg['fgapisrv_ptvendpoint'],
                         'http://localhost/ptv')
        self.assertEqual("%s" % cfg['fgapisrv_ptvuser'], 'ptvuser')
        self.assertEqual("%s" % cfg['fgapisrv_ptvpass'], 'ptvpass')
        self.assertEqual("%s" % cfg['fgapisrv_ptvdefusr'], 'futuregateway')
        self.assertEqual("%s" % cfg['fgapisrv_ptvdefgrp'], 'administrator')
        self.assertEqual("%s" % cfg['fgapisrv_ptvmapfile'],
                         'fgapiserver_ptvmap.json')

    def test_ConfigTypes(self):
        """
        Test that both class defaults and file config settings are matching
        :return:
        """
        self.banner("Check param types")
        cfg = FGApiServerConfig('fgapiserver.conf')
        for param in cfg.keys():
            msg = "Checking type for param: '%s'" % param
            if not (param in cfg.int_types or
                    param in cfg.bool_types):
                print "%s is string" % msg
                self.assertEqual(type(cfg[param]), type(''))
            elif param in cfg.int_types:
                print "%s is integer" % msg
                self.assertEqual(type(cfg[param]), type(1))
            elif param in cfg.bool_types:
                print "%s is boolean" % msg
                self.assertEqual(type(cfg[param]), type(True))
            else:
                print "%s is unexpected (%s)" % (msg, type(param))
                self.assertEqual(0, 1)

    def test_LoadConfig(self):
        """
        Test that both class defaults and file config settings are matching
        :return:
        """
        self.banner("Check param types")
        cfg = FGApiServerConfig('fgapiserver.conf')
        cfg_load = FGApiServerConfig('fgapiserver.conf')
        # Configuration with names and keys matching
        # String types have the key == value
        # Bool types are inverted
        # Integer types are multiplied by -1
        cfg_dict = {
            # FGDB
            "fgapisrv_db_pass": "fgapisrv_db_pass",
            "fgapisrv_db_name": "fgapisrv_db_name",
            "fgapisrv_db_host": "fgapisrv_db_host",
            "fgapisrv_db_port": cfg['fgapisrv_db_port'] * -1,
            "fgapisrv_db_user": "fgapisrv_db_user",
            # fgAPIServer
            "fgapisrv_ptvuser": "fgapisrv_ptvuser",
            "fgapisrv_crt": "fgapisrv_crt",
            "fgapisrv_iosandbox": "fgapisrv_iosandbox",
            "fgapisrv_logcfg": "fgapisrv_logcfg",
            "fgapisrv_host": "fgapisrv_host",
            "fgapisrv_ptvdefgrp": "fgapisrv_ptvdefgrp",
            "fgapisrv_secret": "fgapisrv_secret",
            "fgapiserver_name": "fgapiserver_name",
            "fgapisrv_ptvendpoint": "fgapisrv_ptvendpoint",
            "fgapiver": "fgapiver",
            "fgapisrv_key": "fgapisrv_key",
            "fgjson_indent": cfg['fgjson_indent'] * -1,
            "fgapisrv_notoken": not cfg['fgapisrv_notoken'],
            "fgapisrv_ptvdefusr": "fgapisrv_ptvdefusr",
            "fgapisrv_ptvpass": "fgapisrv_ptvpass",
            "fgapisrv_ptvmapfile": "fgapisrv_ptvmapfile",
            "fgapisrv_notokenusr": "fgapisrv_notokenusr",
            "fgapisrv_dbver": "fgapisrv_dbver",
            "fgapisrv_debug": not cfg['fgapisrv_debug'],
            "fgapisrv_port": cfg['fgapisrv_port'] * -1,
            "fgapisrv_lnkptvflag": not cfg['fgapisrv_lnkptvflag'],
            # GridEngine
            "utdb_user": "utdb_user",
            "utdb_pass": "utdb_pass",
            "utdb_host": "utdb_host",
            "utdb_port": cfg['utdb_port'] * -1,
            "utdb_name": "utdb_name",
            "fgapisrv_geappid": cfg['fgapisrv_geappid'] * -1
        }
        cfg_load.load_config(cfg_dict)

        # Check that all keys and values are matching
        for param in cfg_load.keys():
            print "cfg['%s'] = '%s' <-> cfg_load['%s'] = '%s'" \
                  % (param, cfg[param], param, cfg_load[param])
            if not (param in cfg.int_types or
                    param in cfg.bool_types):
                self.assertEqual(cfg_load[param], param)
            elif param in cfg_load.int_types:
                self.assertEqual(cfg_load[param], -cfg[param])
            elif param in cfg_load.bool_types:
                self.assertEqual(cfg_load[param], not cfg[param])
            else:
                print "Unexpected type: '%s' for parameter: '%s'" \
                      % (type(cfg_load['param']), param)
                self.assertEqual(0, 1)

    def test_EnvOverload(self):
        """
        Test that environment variables are overloading fileconfig settings

        :return:
        """
        self.banner("Evironmnet overloading")

        # Configuration with names and keys matching
        # String types have the key == value
        # Bool types are inverted
        # Integer types are multiplied by -1

        cfg = FGApiServerConfig('fgapiserver.conf')

        cfg_dict = {
            # FGDB
            "fgapisrv_db_pass": "fgapisrv_db_pass",
            "fgapisrv_db_name": "fgapisrv_db_name",
            "fgapisrv_db_host": "fgapisrv_db_host",
            "fgapisrv_db_port": cfg['fgapisrv_db_port'] * -1,
            "fgapisrv_db_user": "fgapisrv_db_user",
            # fgAPIServer
            "fgapisrv_ptvuser": "fgapisrv_ptvuser",
            "fgapisrv_crt": "fgapisrv_crt",
            "fgapisrv_iosandbox": "fgapisrv_iosandbox",
            "fgapisrv_logcfg": "fgapiserver_log.conf",  # This must be '='
            "fgapisrv_host": "fgapisrv_host",
            "fgapisrv_ptvdefgrp": "fgapisrv_ptvdefgrp",
            "fgapisrv_secret": "fgapisrv_secret",
            "fgapiserver_name": "fgapiserver_name",
            "fgapisrv_ptvendpoint": "fgapisrv_ptvendpoint",
            "fgapiver": "fgapiver",
            "fgapisrv_key": "fgapisrv_key",
            "fgjson_indent": cfg['fgjson_indent'] * -1,
            "fgapisrv_notoken": not cfg['fgapisrv_notoken'],
            "fgapisrv_ptvdefusr": "fgapisrv_ptvdefusr",
            "fgapisrv_ptvpass": "fgapisrv_ptvpass",
            "fgapisrv_ptvmapfile": "fgapisrv_ptvmapfile",
            "fgapisrv_notokenusr": "fgapisrv_notokenusr",
            "fgapisrv_dbver": "fgapisrv_dbver",
            "fgapisrv_debug": not cfg['fgapisrv_debug'],
            "fgapisrv_port": cfg['fgapisrv_port'] * -1,
            "fgapisrv_lnkptvflag": not cfg['fgapisrv_lnkptvflag'],
            # GridEngine
            "utdb_user": "utdb_user",
            "utdb_pass": "utdb_pass",
            "utdb_host": "utdb_host",
            "utdb_port": cfg['utdb_port'] * -1,
            "utdb_name": "utdb_name",
            "fgapisrv_geappid": cfg['fgapisrv_geappid'] * -1
        }

        # Set environment variables
        for key in cfg_dict:
            os.environ[key.upper()] = "%s" % cfg_dict[key]

        cfg_new = FGApiServerConfig('fgapiserver.conf')
        for key in cfg_new.keys():
            print "cfg['%s'] = '%s' <-> %s=%s" \
                  % (key, cfg_new[key],
                     key.upper(), os.environ[key.upper()])
            if not (key in cfg_new.int_types or
                    key in cfg_new.bool_types):
                self.assertEqual(cfg_new[key], os.environ[key.upper()])
            elif key in cfg_new.int_types:
                self.assertEqual(cfg_new[key],
                                 int(os.environ[key.upper()]))
            elif key in cfg_new.bool_types:
                self.assertEqual(cfg_new[key],
                                 os.environ[key.upper()].lower() == "true")
            else:
                print "type %s is unexpected" % type(cfg_new[key])
                self.assertEqual(0, 1)

        # Unset environment variables
        for key in cfg_dict:
            del os.environ[key.upper()]


if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main(failfast=True)
