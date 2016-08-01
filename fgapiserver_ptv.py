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

from flask import Flask
from flask import request
from flask import Response
from functools import wraps
from OpenSSL import SSL
from fgapiserverconfig import FGApiServerConfig
import os
import sys
import json
import logging.config

"""
  FutureGateway APIServer front-end
"""

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config = FGApiServerConfig(fgapiserver_config_file)

# fgapiserver settings
fgapiver = fg_config.get_config_value('fgapiver')
fgapiserver_name = fg_config.get_config_value('fgapiserver_name')
fgapisrv_host = fg_config.get_config_value('fgapisrv_host')
fgapisrv_port = int(fg_config.get_config_value('fgapisrv_port'))
fgapisrv_debug = (fg_config.get_config_value(
    'fgapisrv_debug').lower() == 'true')
fgapisrv_iosandbox = fg_config.get_config_value('fgapisrv_iosandbox')
fgapisrv_geappid = int(fg_config.get_config_value('fgapisrv_geappid'))
fgjson_indent = int(fg_config.get_config_value('fgjson_indent'))
fgapisrv_key = fg_config.get_config_value('fgapisrv_key')
fgapisrv_crt = fg_config.get_config_value('fgapisrv_crt')
fgapisrv_logcfg = fg_config.get_config_value('fgapisrv_logcfg')
fgapisrv_dbver = fg_config.get_config_value('fgapisrv_dbver')
fgapisrv_secret = fg_config.get_config_value('fgapisrv_secret')
fgapisrv_notoken = (fg_config.get_config_value(
    'fgapisrv_notoken').lower() == 'true')
fgapisrv_notokenusr = fg_config.get_config_value('fgapisrv_notokenusr')
fgapisrv_lnkptvflag = fg_config.get_config_value('fgapisrv_lnkptvflag')
fgapisrv_ptvendpoint = fg_config.get_config_value('fgapisrv_ptvendpoint')
fgapisrv_ptvuser = fg_config.get_config_value('fgapisrv_ptvuser')
fgapisrv_ptvpass = fg_config.get_config_value('fgapisrv_ptvpass')
fgapisrv_ptvdefusr = fg_config.get_config_value('fgapisrv_ptvdefusr')
fgapisrv_ptvmapfile = fg_config.get_config_value('fgapisrv_ptvmapfile')

# fgapiserver database settings
fgapisrv_db_host = fg_config.get_config_value('fgapisrv_db_host')
fgapisrv_db_port = int(fg_config.get_config_value('fgapisrv_db_port'))
fgapisrv_db_user = fg_config.get_config_value('fgapisrv_db_user')
fgapisrv_db_pass = fg_config.get_config_value('fgapisrv_db_pass')
fgapisrv_db_name = fg_config.get_config_value('fgapisrv_db_name')

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)
logger.debug(fg_config.show_conf())

# setup Flask app
app = Flask(__name__)


##
#  Authentication
##

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    print "Ckecking for: %s - %s" % (username,password)
    return username == fgapisrv_ptvuser and fgapisrv_ptvpass == password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

##
# Self PTV handler
##

#
# /checktoken; PTV normally uses a portal endpoint to verify incoming Tokens
# Portals normally return a json in the format:
#    { "token_status": "<valid|invalid>",
#    ["portal_user": "<portal_username>"
#     "portal_group": "<portal user group name>" ] }
# Optional fields portal_user and portal_groups are used to map the portal
# user/group with a FutureGateway user/group
# This self PTV handler totally ignores basic authentication credentials
# (username/password) contained in the request form
#
@app.route('/checktoken', methods=['GET', 'POST'])
@app.route('/%s/checktoken' % fgapiver, methods=['GET', 'POST'])
@requires_auth
def checktoken():
    response = {}
    token = request.values.get('token')
    if request.method == 'GET':
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    elif request.method == 'POST':
        response = {
            "token_status": "valid",
            # you may specify:
            #  portal_user - A portal user that can be mapped by
            #                fgapiserver_ptvmap.json map file
            #  portal_group - A portal group that can be mapped by
            #                 fgapiserver_ptvmap.json map file
            #"portal_user": fgapisrv_ptvdefusr
            "portal_group": "admin"
        }
        ctk_status = 200
    else:
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/checktoken"}, ]
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=ctk_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp

##
# Auth handlers
##


# Common header section


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Server', fgapiserver_name)
    return response


#
# The app starts here
#

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    if len(fgapisrv_crt) > 0 and len(fgapisrv_key) > 0:
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(fgapisrv_key)
        context.use_certificate_file(fgapisrv_crt)
        app.run(host=fgapisrv_host, port=fgapisrv_port,
                ssl_context=context, debug=fgapisrv_debug)
    else:
        app.run(host=fgapisrv_host, port=fgapisrv_port+1, debug=fgapisrv_debug)
