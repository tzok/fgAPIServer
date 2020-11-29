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
from fgapiserver_config import FGApiServerConfig
import os
import sys
import json
import logging.config
from fgapiserver_tools import check_api_ver

"""
  FutureGateway APIServer front-end
"""

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10.1'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-10-18 15:19:14'

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config = FGApiServerConfig(fgapiserver_config_file)

# Logging
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])
logger = logging.getLogger(__name__)

# setup Flask app
app = Flask(__name__)


##
#  Authentication
##


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    print("Ckecking for: %s - %s" % (username, password))
    return (username == fg_config['fgapisrv_ptvuser'] and
            password == fg_config['fgapisrv_ptvpass'])


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


##
# Test helper functions
##

token_file = '.iam/token'
default_token = ("eyJraWQiOiJyc2ExIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIzYTJkN"
                 "BmNS0zYmRjLTQwMjAtODJjYi0xMDI4OTQzYzc3N2QiLCJpc3MiOiJodH"
                 "wczpcL1wvaWFtLXRlc3QuaW5kaWdvLWRhdGFjbG91ZC5ldVwvIiwiZXh"
                 "IjoxNDc2MjY3NjA2LCJpYXQiOjE0NzYyNjQwMDYsImp0aSI6IjRjN2Y5"
                 "TczLWJmYzItNDEzYy1hNzhjLWUxZmJlMGU2NjAwYSJ9.BfDlr6Far_oe"
                 "7z-SuLPbXgfKx3VuHJ0iuL-Dyd6G5_7_rNPrvZr5Da_HJUfonOLr8uOo"
                 "UhMUIP_Xiw4ZuWVIIhNPDSdu4lhWy5kkcoQ3rI9myNT2WxLA3IP2ZEwP"
                 "InefF0LzAlMj4-iQQw-kAavKgvA00sO8cww9Hzx6Thfw")


def get_token_file(tokenfile):
    """This function returns the token stored in the given token_file"""
    token = default_token
    try:
        tkn_f = open(tokenfile, 'rt')
        token = tkn_f.read()[:-1]
        tkn_f.close()
    except IOError:
        print("Token file '%s' could not be accessed; using default"
              % tokenfile)
    return token


subject_file = '.iam/subject'
default_subject = '98e3009e-e39b-11e6-bcba-5eef910c8578'


def get_subject_file(subjectfile):
    """This function returns the subject stored in the given subject_file"""
    subject = default_subject
    try:
        sbj_f = open(subjectfile)
        subject = sbj_f.read()[:-1]
        sbj_f.close()
    except IOError:
        print("Subject file '%s' could not be accessed; using default"
              % subjectfile)
    return subject


groups_file = '.iam/groups'
default_groups = ['Admin',
                  'Developers']


def get_groups_file(groupsfile):
    """This function returns the groups stored in the given groups file"""
    groups = default_groups
    try:
        grp_f = open(groupsfile)
        groups = [grp[:-1] for grp in grp_f]
        grp_f.close()
    except IOError:
        print("Groups file '%s' could not be accessed; using default"
              % groupsfile)
    return groups

##
# PTV handlers
##


#
# /get-token; PTV endpoint to retrieve a new valid token
# Portals normally return a json in the format:
#    {
#        "error": null,
#        "groups": null,
#        "subject": "<the-subject>",
#        "token": "<the-new-token>"
#    }
# This PTV handler totally ignores basic authentication credentials
# (username/password) contained in the request form but needs the
# subject field initially returned by the checktoken/ call
#
@app.route('/get-token', methods=['GET', 'POST'])
@app.route('/<apiver>/get-token', methods=['GET', 'POST'])
@requires_auth
def get_token(apiver=fg_config['fgapiver']):
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        response = {}
        subject = request.values.get('subject')
        if request.method == 'GET':
            message = "Unhandled method: '%s'" % request.method
            response["error"] = message
            status = 400
        elif request.method == 'POST':
            response = {
                "error": None,
                "groups": get_groups_file(groups_file),
                "subject": subject,
                "token": get_token_file(token_file)
            }
            status = 200
        else:
            message = "Unhandled method: '%s'" % request.method
            response["error"] = message
            status = 400
        # include _links part
        response["_links"] = [{"rel": "self", "href": "/get-token"}, ]
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


#
# /checktoken; PTV normally uses a portal endpoint to verify incoming Tokens
# Portals normally return a json in the format:
#    { "token_status": "<valid|invalid>",
#    ["portal_user": "<portal_username>"
#     "portal_group": "<portal user group name>" ] }
# Optional fields portal_user and portal_groups are used to map the portal
# user/group with a FutureGateway user/group
# This PTV handler totally ignores basic authentication credentials
# (username/password) contained in the request form
#
@app.route('/get-token-info', methods=['GET', 'POST'])
@app.route('/<apiver>/get-token-info', methods=['GET', 'POST'])
@app.route('/checktoken', methods=['GET', 'POST'])
@app.route('/<apiver>/checktoken', methods=['GET', 'POST'])
@requires_auth
def checktoken(apiver=fg_config['fgapiver']):
    logger.debug('Tocken check(%s): %s'
                 % (request.method, request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        response = {}
        token = request.values.get('token')
        if request.method == 'GET':
            message = "Unhandled method: '%s'" % request.method
            response["error"] = message
            status = 400
        elif request.method == 'POST':
            # response = {
            #    "token_status": "valid",
            #    # you may specify:
            #    #  portal_user - A portal user that can be mapped by
            #    #                fgapiserver_ptvmap.json map file
            #    #  portal_group - A portal group that can be mapped by
            #    #                 fgapiserver_ptvmap.json map file
            #    # "portal_user": fgapisrv_ptvdefusr
            #    "portal_group": "admin"
            # }
            response = {
                "error": None,
                "groups": get_groups_file(groups_file),
                "subject": get_subject_file(subject_file),
                "token": token
            }
            status = 200
        else:
            message = "Unhandled method: '%s'" % request.method
            response["error"] = message
            status = 400
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/checktoken"}, ]
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


##
# Orchestrator test handler
##


def create_inprogress():
    return {
        "uuid": "756ed6b2-ed63-4992-a8f8-8d5d8045ae02",
        "creationTime": "2016-08-01T12:47+0000",
        "status": "CREATE_IN_PROGRESS",
        "outputs": {},
        "task": "NONE",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/template")
            }
        ]
    }, 201


def create_failed():
    return {
        "uuid": "756ed6b2-ed63-4992-a8f8-8d5d8045ae02",
        "creationTime": "2016-08-01T12:47+0000",
        "updateTime": "2016-08-01T12:47+0000",
        "status": "CREATE_FAILED",
        "statusReason": ("Error 400: Error Creating Inf.: "
                         "Some deploys did not proceed "
                         "successfully: All machines could not be "
                         "launched: \nAttempt 1: Error launching the VMs of "
                         "type ambertools_server to cloud ID one of type "
                         "OpenNebula. Cloud Provider "
                         "Error: No ONE network found for network: "
                         "public_net\n"
                         "Attempt 2: Error launching the VMs of type "
                         "ambertools_server to cloud ID one of type "
                         "OpenNebula. "
                         "Cloud Provider Error: No ONE network found for "
                         "network:  public_net\nAttempt 3: Error "
                         "launching the "
                         "VMs of type ambertools_server to cloud ID one of "
                         " type OpenNebula.  Cloud Provider Error: No ONE "
                         "network found for network: public_net\n\n"),
        "outputs": {},
        "task": "NONE",
        "cloudProviderName": "provider-UPV-GRyCAP",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/template")
            }
        ]
    }, 200


def create_badreq():
    return {
        "code": 400,
        "title": "Bad Request",
        "message": ("Failed to replace input function on "
                    "<node_templates[...][...][X]>, caused by: No "
                    "input provided for <x> and no default value provided in "
                    "the definition")
    }, 400


def create_complete():
    return {
        "uuid": "1bff4c04-e8b7-43be-8846-a39df1664433",
        "creationTime": "2016-04-12T19:34+0000",
        "updateTime": "2016-04-12T19:38+0000",
        "status": "CREATE_COMPLETE",
        "outputs": {
            "node_creds": "{password=7Uxz4RJR, user=jobtest}",
            "node_ip": "localhost"
        },
        "task": "NONE",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433/template")
            }
        ]
    }, 200


def check_input():
    return {
        "parameters": {
            "number_cpus": 1,
            "memory_size": "1 GB"
        },
        "template": (
            "tosca_definitions_version: tosca_simple_yaml_1_0\n\n"
            "imports:\n - indigo_custom_types: "
            "https://raw.githubusercontent.com/indigo-dc/tosca-types"
            "/master/custom_types.yaml\n\ndescription: TOSCA template "
            "for deploying an instance of AmberTools v15\n"
            "\ntopology_template:\n"
            " inputs:\n number_cpus:\n type: integer\n "
            "description: number of cpus required for the instance\n "
            "default: 1\n memory_size:\n type: string\n description: "
            "ram memory required for the instance\n default: 1 GB\n\n "
            "node_templates:\n\n ambertools:\n type: tosca.nodes.indigo."
            "Ambertools\n requirements:\n - host: ambertools_server\n\n "
            "ambertools_server:\n type: tosca.nodes.indigo.Compute\n "
            "capabilities:\n endpoint:\n properties:\n network_name: "
            "PUBLIC\n ports:\n ssh_port:\n protocol: tcp\n source: 22\n "
            "host:\n properties:\n num_cpus: { get_input: number_cpus }\n "
            "mem_size: { get_input: memory_size }\n os:\n properties:\n "
            "type: linux\n distribution: ubuntu\n version: 14.04\n "
            "image: indigodatacloudapps/ambertools\n\n outputs:\n "
            "instance_ip:\n value: { get_attribute: [ ambertools_server, "
            "public_address, 0 ] }\n instance_creds:\n value: { "
            "get_attribute: [ ambertools_server, endpoint, credential,"
            " 0 ] }")
    }


@app.route('/orchestrator/deployments/<uuid>', methods=['GET', 'DELETE'])
def orchestrator_deployments_get(uuid):
    response = {}
    dep_status = 404
    token = request.headers.get('Authorization')
    if request.method == 'GET':
        print("endpoint: /orchestrator/deployments/%s (GET)" % uuid)
        print("token: %s" % token)
        response, dep_status = create_complete()
        # response, dep_status = create_inprogress()
        # response, dep_status = create_failed()
    elif request.method == 'DELETE':
        print("endpoint: /orchestrator/deployments/%s (DELETE)" % uuid)
        dep_status = 404
        response = {"error": "Method not yet implemented"}
    print("response: '%s'" % response)
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=dep_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@app.route('/orchestrator/deployments', methods=['POST'])
def orchestrator_deployments():
    response = {}
    dep_status = 404
    token = request.headers.get('Authorization')
    if request.method == 'GET':
        dep_status = 404
        response = {"error": "Method not supported"}
    elif request.method == 'POST':
        print("endpoint: /orchestrator/deployments (POST)")
        print("token: %s" % token)
        # Enable below lines for successful deployment
        response, dep_status = create_inprogress()
        print("Returned create in progress: '%s' (%s)"
              % (response, dep_status))
        # Enable below lnes for failed request due to bad request
        # response, dep_status = create_badreq()
        # print("Returned bad request: '%s' (%s)" % (response, dep_status))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=dep_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


# Common header section


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Server', fg_config['fgapiserver_name'])
    return response


#
# The app starts here
#

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    if len(fg_config['fgapisrv_crt']) > 0 and \
            len(fg_config['fgapisrv_key']) > 0:
        context = (fg_config['fgapisrv_crt'],
                   fg_config['fgapisrv_key'])
        app.run(host=fg_config['fgapisrv_host'],
                port=fg_config['fgapisrv_port']+1,
                ssl_context=context,
                debug=fg_config['fgapisrv_debug'])
    else:
        app.run(host=fg_config['fgapisrv_host'],
                port=fg_config['fgapisrv_port']+1,
                debug=fg_config['fgapisrv_debug'])
