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

from flask import request
from flask import Response
from flask import Blueprint
from flask_login import LoginManager, UserMixin, login_required, current_user
from fgapiserverconfig import FGApiServerConfig
from fgapiserverdb import FGAPIServerDB
import os
import sys
import json
import logging

"""
  FutureGateway APIServer User class
"""
__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.7-1"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

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

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)


class User(UserMixin):
    """
    FG User object inherited from Flask User object
    """

    """
    Logging
    """
    log = None

    """
    flask-login User Class
    """

    log = None
    id = 0
    name = ''

    def load_config(self):
        # setup path
        fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # fgapiserver configuration file
        fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

        # Load configuration
        fg_config_obj = FGApiServerConfig(fgapiserver_config_file)
        fg_config = fg_config_obj.get_config()

        # fgapiserver settings
        self.fgapiver = fg_config['fgapiver']
        self.fgapiserver_name = fg_config['fgapiserver_name']
        self.fgapisrv_host = fg_config['fgapisrv_host']
        self.fgapisrv_port = int(fg_config['fgapisrv_port'])
        self.fgapisrv_debug = fg_config['fgapisrv_debug'].lower() == 'true'
        self.fgapisrv_iosandbox = fg_config['fgapisrv_iosandbox']
        self.fgapisrv_geappid = int(fg_config['fgapisrv_geappid'])
        self.fgjson_indent = int(fg_config['fgjson_indent'])
        self.fgapisrv_key = fg_config['fgapisrv_key']
        self.fgapisrv_crt = fg_config['fgapisrv_crt']
        self.fgapisrv_logcfg = fg_config['fgapisrv_logcfg']
        self.fgapisrv_dbver = fg_config['fgapisrv_dbver']
        self.fgapisrv_secret = fg_config['fgapisrv_secret']
        self.fgapisrv_notoken = fg_config['fgapisrv_notoken'].lower() == 'true'
        self.fgapisrv_notokenusr = fg_config['fgapisrv_notokenusr']
        self.fgapisrv_lnkptvflag = fg_config['fgapisrv_lnkptvflag']
        self.fgapisrv_ptvendpoint = fg_config['fgapisrv_ptvendpoint']
        self.fgapisrv_ptvuser = fg_config['fgapisrv_ptvuser']
        self.fgapisrv_ptvpass = fg_config['fgapisrv_ptvpass']
        self.fgapisrv_ptvdefusr = fg_config['fgapisrv_ptvdefusr']
        self.fgapisrv_ptvdefgrp = fg_config['fgapisrv_ptvdefgrp']
        self.fgapisrv_ptvmapfile = fg_config['fgapisrv_ptvmapfile']

        # fgapiserver database settings
        self.fgapisrv_db_host = fg_config['fgapisrv_db_host']
        self.fgapisrv_db_port = int(fg_config['fgapisrv_db_port'])
        self.fgapisrv_db_user = fg_config['fgapisrv_db_user']
        self.fgapisrv_db_pass = fg_config['fgapisrv_db_pass']
        self.fgapisrv_db_name = fg_config['fgapisrv_db_name']

    def __init__(self, id, name):
        self.log = logging.getLogger(__name__)
        self.id = id
        self.name = name
        self.log.debug("fgUser - id: '%s' - name: '%s'" % (id, name))
        self.load_config()
        self.get_fgapiserver_db()

    def get_id(self):
        """
         Get the user identifier
        :return: user_id
        """
        return self.id

    def get_name(self):
        """
         Get the user name
        :return:  user_name
        """
        return self.name

    def get_fgapiserver_db(self):
        """
        Retrieve the fgAPIServer database object

        :return: Return the fgAPIServer database object or None if the
             database connection fails
        """
        self.fgapisrv_db = FGAPIServerDB(
            db_host=self.fgapisrv_db_host,
            db_port=self.fgapisrv_db_port,
            db_user=self.fgapisrv_db_user,
            db_pass=self.fgapisrv_db_pass,
            db_name=self.fgapisrv_db_name,
            iosandbbox_dir=self.fgapisrv_iosandbox,
            fgapiserverappid=self.fgapisrv_geappid)
        db_state = self.fgapisrv_db.get_state()
        if db_state[0] != 0:
            logger.error("Unbable to connect to the database:\n"
                         "  host: %s\n"
                         "  port: %s\n"
                         "  user: %s\n"
                         "  pass: %s\n"
                         "  name: %s\n"
                         % (self.fgapisrv_db_host,
                            self.fgapisrv_db_port,
                            self.fgapisrv_db_user,
                            self.fgapisrv_db_pass,
                            self.fgapisrv_db_name))
            return None
        return self.fgapisrv_db


user_api = Blueprint('user_api', __name__, template_folder='templates')


@user_api.route('/%s/user/<user>' % fgapiver, methods=['GET', 'POST'])
@login_required
def user(user):

    logging.debug('user(%s)/%s: %s' % (request.method,
                                       user,
                                       request.values.to_dict()))
    u = User(0, user)
    if request.method == 'GET':
        if u.fgapisrv_db.user_exists(user):
            user_record = u.fgapisrv_db.user_retrieve(user)
            status = 200
            response = user_record
        else:
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
    elif request.method == 'POST':
        if u.fgapisrv_db.user_exists(user):
            user_record = u.fgapisrv_db.user_retrieve(user)
            status = 200
            response = user_record
        else:
            params = request.get_json()
            logger.debug("params: '%s'" % params)
            if params is not None:
                user_data = {
                    'first_name': params.get('first_name', ''),
                    'last_name': params.get('last_name', ''),
                    'name': user,
                    'institute': params.get('institute', ''),
                    'mail': params.get('mail', ''),
                }
                user_record = u.fgapisrv_db.user_create(user_data)
                if user_record is not None:
                    status = 201
                    response = user_record
                else:
                    status = 400
                    response = {
                        'message': 'Unable to create user \'%s\'' % user
                    }
            else:
                status = 400
                response = {
                    'message': 'Missing userdata'
                }
    else:
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=u.fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp
