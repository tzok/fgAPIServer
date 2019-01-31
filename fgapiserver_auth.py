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

from fgapiserverdb import FGAPIServerDB
from fgapiserverconfig import FGApiServerConfig

import os
import sys
import logging.config

"""
  FutureGateway APIServer authN/Z functions
"""

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.7-1"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"
__status__ = "release"
__update__ = "23-05-2017 17:23:15"


# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config_obj = FGApiServerConfig(fgapiserver_config_file)
fg_config = fg_config_obj.get_config()

# fgapiserver settings
fgapiver = fg_config['fgapiver']
fgapiserver_name = fg_config['fgapiserver_name']
fgapisrv_host = fg_config['fgapisrv_host']
fgapisrv_port = int(fg_config['fgapisrv_port'])
fgapisrv_debug = fg_config['fgapisrv_debug'].lower() == 'true'
fgapisrv_iosandbox = fg_config['fgapisrv_iosandbox']
fgapisrv_geappid = int(fg_config['fgapisrv_geappid'])
fgjson_indent = int(fg_config['fgjson_indent'])
fgapisrv_key = fg_config['fgapisrv_key']
fgapisrv_crt = fg_config['fgapisrv_crt']
fgapisrv_logcfg = fg_config['fgapisrv_logcfg']
fgapisrv_dbver = fg_config['fgapisrv_dbver']
fgapisrv_secret = fg_config['fgapisrv_secret']
fgapisrv_notoken = fg_config['fgapisrv_notoken'].lower() == 'true'
fgapisrv_notokenusr = fg_config['fgapisrv_notokenusr']
fgapisrv_lnkptvflag = fg_config['fgapisrv_lnkptvflag']
fgapisrv_ptvendpoint = fg_config['fgapisrv_ptvendpoint']
fgapisrv_ptvuser = fg_config['fgapisrv_ptvuser']
fgapisrv_ptvpass = fg_config['fgapisrv_ptvpass']
fgapisrv_ptvdefusr = fg_config['fgapisrv_ptvdefusr']
fgapisrv_ptvdefgrp = fg_config['fgapisrv_ptvdefgrp']
fgapisrv_ptvmapfile = fg_config['fgapisrv_ptvmapfile']

# fgapiserver database settings
fgapisrv_db_host = fg_config['fgapisrv_db_host']
fgapisrv_db_port = int(fg_config['fgapisrv_db_port'])
fgapisrv_db_user = fg_config['fgapisrv_db_user']
fgapisrv_db_pass = fg_config['fgapisrv_db_pass']
fgapisrv_db_name = fg_config['fgapisrv_db_name']

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)


def get_fgapiserver_db():
    """
    Retrieve the fgAPIServer database object

    :return: Return the fgAPIServer database object or None if the
             database connection fails
    """
    apiserver_db = FGAPIServerDB(
        db_host=fgapisrv_db_host,
        db_port=fgapisrv_db_port,
        db_user=fgapisrv_db_user,
        db_pass=fgapisrv_db_pass,
        db_name=fgapisrv_db_name,
        iosandbbox_dir=fgapisrv_iosandbox,
        fgapiserverappid=fgapisrv_geappid)
    db_state = apiserver_db.get_state()
    if db_state[0] != 0:
        logger.error("Unbable to connect to the database:\n"
                     "  host: %s\n"
                     "  port: %s\n"
                     "  user: %s\n"
                     "  pass: %s\n"
                     "  name: %s\n"
                     % (fgapisrv_db_host,
                        fgapisrv_db_port,
                        fgapisrv_db_user,
                        fgapisrv_db_pass,
                        fgapisrv_db_name))
        return None
    return apiserver_db


def authorize_user(current_user, app_id, user, reqroles):
    """
    This function returns true if the given user is authorized to process the
    requested action
    The request will be checked against user group roles stored in the database

    :param current_user: The user requesting the action
    :param app_id: The application id (if appliable)
    :param user: The user specified by the filter
    :param reqroles: The requested roles: task_view, app_run, ...
    :return:
    """
    logger.debug("AuthUser: (begin)")
    global fgapisrv_db

    # Return True if token management is disabled
    # if fgapisrv_notoken:
    #     return True, 'Authorization disabled'

    message = ''
    user_id = current_user.get_id()
    user_name = current_user.get_name()
    logger.debug(("AuthUser: user_id: '%s' - "
                  "user_name: '%s'" % (user_id, user_name)))

    # Check if requested action is in the user group roles
    auth_z = fgapisrv_db.verify_user_role(user_id, reqroles)
    logger.debug(("AuthUser: Auth for user '%s' "
                  "with roles '%s' is %s")
                 % (user_id, reqroles, auth_z))
    if not auth_z:
        message = ("User '%s' does not have requested '%s' role(s)\n"
                   % (user_name, reqroles))
    # Check current_user and filter user are different
    if user_name != user:
        logger.debug("AuthUser: User name '%s' differs from user '%s'"
                     % (user_name, user))
        user_impersonate = fgapisrv_db.verify_user_role(
            user_id, 'user_impersonate')
        if user != "@":
            group_impersonate = fgapisrv_db.same_group(
                user_name, user) and fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
        else:
            group_impersonate = fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
        auth_z = auth_z and (user_impersonate or group_impersonate)
        if not auth_z:
            if user == "*":
                user_text = "any user"
            elif user == "@":
                user_text = "group-wide users"
            else:
                user_text = "'%s' user" % user
            message = "User '%s' cannot impersonate %s\n" % (
                user_name, user_text)
    # Check if app belongs to Group apps
    if app_id is not None:
        logger.debug("AuthUser: checking for app_id '%s'" % app_id)
        auth_z = auth_z and fgapisrv_db.verify_user_app(user_id, app_id)
        if not auth_z:
            message = ("User '%s' cannot perform any activity on application "
                       "having id: '%s'\n") % (user_name, app_id)
    return auth_z, message


# Get the database object
fgapisrv_db = get_fgapiserver_db()
