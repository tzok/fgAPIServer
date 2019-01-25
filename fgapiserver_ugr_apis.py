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
  FutureGateway APIServer User, Group and Roles APIs
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
    fgapisrv_db = FGAPIServerDB(
        db_host=fgapisrv_db_host,
        db_port=fgapisrv_db_port,
        db_user=fgapisrv_db_user,
        db_pass=fgapisrv_db_pass,
        db_name=fgapisrv_db_name,
        iosandbbox_dir=fgapisrv_iosandbox,
        fgapiserverappid=fgapisrv_geappid)
    db_state = fgapisrv_db.get_state()
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
    return fgapisrv_db


# Define Blueprint for user groups and roles APIs
ugr_apis = Blueprint('ugr_apis', __name__, template_folder='templates')

# Get the database object
fgapisrv_db = get_fgapiserver_db()


@ugr_apis.route('/%s/users' % fgapiver, methods=['GET', 'POST'])
@login_required
def users():
    global fgapisrv_db

    logging.debug('users(%s): %s' % (request.method,
                                     request.values.to_dict()))
    if request.method == 'GET':
        user_record = fgapisrv_db.users_retrieve()
        status = 200
        response = {"users": user_record}
    elif request.method == 'POST':
        params = request.get_json()
        logger.debug("params: '%s'" % params)
        if params is not None:
            user_data = {
                'first_name': params.get('first_name', ''),
                'last_name': params.get('last_name', ''),
                'name': params.get('name', ''),
                'institute': params.get('institute', ''),
                'mail': params.get('mail', ''),
            }
            user_record = fgapisrv_db.user_create(user_data)
            if user_record is not None:
                status = 201
                response = user_record
            else:
                status = 400
                response = {
                    'message': 'Unable to create user \'%s\'' % user_data
                }
        else:
            status = 400
            response = {
                'message': 'Missing userdata'
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/users/<user>' % fgapiver, methods=['GET', 'POST'])
@login_required
def users_user(user):
    global fgapisrv_db

    logging.debug('users(%s)/%s: %s' % (request.method,
                                        user,
                                        request.values.to_dict()))
    if request.method == 'GET':
        if fgapisrv_db.user_exists(user):
            user_record = fgapisrv_db.user_retrieve(user)
            status = 200
            response = user_record
        else:
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
    elif request.method == 'POST':
        if fgapisrv_db.user_exists(user):
            user_record = fgapisrv_db.user_retrieve(user)
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
                user_record = fgapisrv_db.user_create(user_data)
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
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/users/<user>/groups' % fgapiver,
                methods=['GET', 'POST', 'DELETE'])
@login_required
def user_groups(user):
    global fgapisrv_db

    logging.debug('user_groups(%s)/%s: %s' % (request.method,
                                              user,
                                              request.values.to_dict()))
    if request.method == 'GET':
        if fgapisrv_db.user_exists(user):
            group_list = fgapisrv_db.user_groups_retrieve(user)
            status = 200
            response = {'groups':  group_list}
        else:
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
    elif request.method == 'POST':
        if not fgapisrv_db.user_exists(user):
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
        else:
            params = request.get_json()
            logger.debug("params: '%s'" % params)
            if params is not None:
                group_list = params.get('groups', [])
                inserted_groups = fgapisrv_db.add_user_groups(user, group_list)
                if inserted_groups is not None:
                    status = 201
                    response = {'groups': inserted_groups}
                else:
                    status = 400
                    response = {
                        'message':
                            'Unable to assign groups %s to user \'%s\'' %
                            (group_list, user)
                    }
            else:
                status = 400
                response = {
                    'message': 'Missing groups'
                }
    elif request.method == 'DELETE':
        if not fgapisrv_db.user_exists(user):
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
        else:
            params = request.get_json()
            logger.debug("params: '%s'" % params)
            if params is not None:
                group_list = params.get('groups', [])
                deleted_groups = fgapisrv_db.delete_user_groups(user,
                                                                group_list)
                if deleted_groups is not None:
                    status = 200
                    response = {'groups': deleted_groups}
                else:
                    status = 400
                    response = {
                        'message':
                            'Unable to delete groups %s to user \'%s\'' %
                            (group_list, user)
                    }
            else:
                status = 400
                response = {
                    'message': 'Missing groups'
                }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/users/<user>/tasks' % fgapiver, methods=['GET', ])
@login_required
def user_tasks(user):
    global fgapisrv_db

    logging.debug('user_tasks(%s)/%s: %s' % (request.method,
                                             user,
                                             request.values.to_dict()))
    application = request.values.get('application')

    if request.method == 'GET':
        if fgapisrv_db.user_exists(user):
            tasks_list = []
            user_task_ids = fgapisrv_db.user_tasks_retrieve(user, application)
            for task_id in user_task_ids:
                task_record = fgapisrv_db.get_task_record(task_id)
                tasks_list += [task_record, ]
            status = 200
            response = {'tasks':  tasks_list}
        else:
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route(
    '/%s/users/<user>/tasks/<task_id>' % fgapiver, methods=['GET', ])
@login_required
def user_tasks_id(user, task_id):
    global fgapisrv_db

    logging.debug('user_tasks(%s)/%s: %s' % (request.method,
                                             user,
                                             request.values.to_dict()))

    if request.method == 'GET':
        if fgapisrv_db.user_exists(user):
            response = fgapisrv_db.get_task_record(task_id)
            status = 200
        else:
            status = 404
            response = {
                'message': 'User \'%s\' does not exists' % user
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/groups' % fgapiver, methods=['GET', 'POST'])
@login_required
def groups():
    global fgapisrv_db

    logging.debug('groups(%s): %s' % (request.method,
                                      request.values.to_dict()))
    if request.method == 'GET':
        group_list = fgapisrv_db.groups_retrieve()
        status = 200
        response = {'groups': group_list}
    elif request.method == 'POST':
        params = request.get_json()
        if params is not None:
            logger.debug("params: '%s'" % params)
            group_name = params.get('name', '')
            new_group = fgapisrv_db.group_add(group_name)
            if new_group is not None:
                status = 201
                response = new_group
            else:
                status = 400
                response = {
                    'message':
                    'Unable to create group: \'%s\'' % group_name
                }
        else:
            status = 400
            response = {
                'message': 'Missing group'
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/groups/<group>' % fgapiver, methods=['GET', 'POST'])
@login_required
def groups_group(group):
    global fgapisrv_db

    logging.debug('groups_group(%s)/%s: %s' % (request.method,
                                               group,
                                               request.values.to_dict()))
    if request.method == 'GET':
        group_info = fgapisrv_db.group_retrieve(group)
        if group_info is not None:
            status = 200
            response = group_info
        else:
            status = 404
            response = {
                'message': 'No groups found with name or id: %s' % group}
    elif request.method == 'POST':
        status = 404
        response = {"message": "Not yet implemented"}
    else:
        status = 404
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/groups/<group>/apps' % fgapiver, methods=['GET', 'POST'])
@login_required
def groups_group_apps(group):
    global fgapisrv_db

    logging.debug('groups_group_apps(%s)/%s: %s' % (request.method,
                                                    group,
                                                    request.values.to_dict()))
    if request.method == 'GET':
        group_apps_info = fgapisrv_db.group_apps_retrieve(group)
        if group_apps_info is not None:
            status = 200
            response = group_apps_info
        else:
            status = 404
            response = {
                'message': ('No applications found for group having name or '
                            'id: %s' % group)}
    elif request.method == 'POST':
        params = request.get_json()
        if params is not None:
            logger.debug("params: '%s'" % params)
            app_ids = params.get('applications', [])
            new_ids = fgapisrv_db.group_apps_add(group, app_ids)
            if new_ids != []:
                status = 201
                response = {'applications': new_ids}
            else:
                status = 400
                response = {
                    'message':
                    ('Unable to associate applications \'%s\' '
                     'to the group: \'%s\'' % (app_ids,
                                               group))
                }
        else:
            status = 400
            response = {
                'message': 'Missing group'
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/groups/<group>/roles' % fgapiver, methods=['GET', 'POST'])
@login_required
def groups_group_roles(group):
    global fgapisrv_db

    logging.debug('groups_group_roles(%s)/%s: %s' % (request.method,
                                                     group,
                                                     request.values.to_dict()))
    if request.method == 'GET':
        group_roles_info = fgapisrv_db.group_roles_retrieve(group)
        if group_roles_info is not None:
            status = 200
            response = group_roles_info
        else:
            status = 404
            response = {
                'message': ('No roles found for group having name or '
                            'id: %s' % group)}
    elif request.method == 'POST':
        params = request.get_json()
        if params is not None:
            logger.debug("params: '%s'" % params)
            role_ids = params.get('roles', [])
            new_roles = fgapisrv_db.group_apps_add(group, role_ids)
            if new_roles != []:
                status = 201
                response = {'roles': new_roles}
            else:
                status = 400
                response = {
                    'message':
                    ('Unable to roles \'%s\' '
                     'to the group: \'%s\'' % (role_list,
                                               group))
                }
        else:
            status = 400
            response = {
                'message': 'Missing group'
            }
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/%s/roles' % fgapiver, methods=['GET', ])
@login_required
def roles():
    global fgapisrv_db

    logging.debug('groups(%s): %s' % (request.method,
                                      request.values.to_dict()))
    if request.method == 'GET':
        role_list = fgapisrv_db.roles_retrieve()
        status = 200
        response = {'roles': role_list}
    else:
        status = 400
        response = {"message": "Unhandled method: '%s'" % request.method}

    logger.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp
