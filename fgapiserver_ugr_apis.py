#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from flask_login import login_required, current_user
from fgapiserver_config import fg_config
from fgapiserver_db import fgapisrv_db
from fgapiserver_auth import authorize_user
from fgapiserver_tools import check_api_ver
import json
import logging

"""
  FutureGateway APIServer User, Group and Roles APIs
"""
__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-05-27 11:23:18'

# Logging
logger = logging.getLogger(__name__)

# Define Blueprint for user groups and roles APIs
ugr_apis = Blueprint('ugr_apis', __name__, template_folder='templates')


@ugr_apis.route('/<apiver>/users', methods=['GET', 'POST'])
@login_required
def users(apiver=fg_config['fgapiver']):

    logging.debug('users(%s): %s' % (request.method,
                                     request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_view")
            if auth_state is True:
                user_record = fgapisrv_db.users_retrieve()
                status = 200
                response = {"users": user_record}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_change")
            if auth_state is True:
                params = request.get_json()
                logging.debug("params: '%s'" % params)
                new_users = []
                if params is not None:
                    user_records = params.get('users', [])
                    for user_data in user_records:
                        user_record = fgapisrv_db.user_create(user_data)
                        if user_record is not None:
                            new_users.append(user_record)
                    if new_users is not []:
                        status = 201
                        response = {"users": new_users}
                    else:
                        status = 400
                        response = {
                            'message': 'Unable to create user(s) \'%s\''
                                       % user_records
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing userdata'
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg
                }
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/users/<user>', methods=['GET', 'POST'])
@login_required
def users_user(user, apiver=fg_config['fgapiver']):

    logging.debug('users(%s)/%s: %s' % (request.method,
                                        user,
                                        request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_view")
            if auth_state is True:
                if fgapisrv_db.user_exists(user):
                    user_record = fgapisrv_db.user_retrieve(user)
                    status = 200
                    response = user_record
                else:
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_change")
            if auth_state is True:
                if fgapisrv_db.user_exists(user):
                    user_record = fgapisrv_db.user_retrieve(user)
                    status = 200
                    response = user_record
                else:
                    params = request.get_json()
                    logging.debug("params: '%s'" % params)
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
                                'message': 'Unable to create user \'%s\''
                                           % user
                            }
                    else:
                        status = 400
                        response = {
                            'message': 'Missing userdata'
                        }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/users/<user>/groups',
                methods=['GET', 'POST', 'DELETE'])
@login_required
def user_groups(user, apiver=fg_config['fgapiver']):

    logging.debug('user_groups(%s)/%s: %s' % (request.method,
                                              user,
                                              request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_groups_view")
            if auth_state is True:
                if fgapisrv_db.user_exists(user):
                    group_list = fgapisrv_db.user_groups_retrieve(user)
                    status = 200
                    response = {'groups': group_list}
                else:
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_groups_change")
            if auth_state is True:
                if not fgapisrv_db.user_exists(user):
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
                else:
                    params = request.get_json()
                    logging.debug("params: '%s'" % params)
                    if params is not None:
                        group_list = params.get('groups', [])
                        inserted_groups =\
                            fgapisrv_db.add_user_groups(user, group_list)
                        if inserted_groups is not None:
                            status = 201
                            response = {'groups': inserted_groups}
                        else:
                            status = 400
                            response = {
                                'message':
                                    ('Unable to assign groups %s '
                                     'to user \'%s\'') %
                                    (group_list, user)
                            }
                    else:
                        status = 400
                        response = {
                            'message': 'Missing groups'
                        }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'DELETE':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_groups_change")
            if auth_state is True:
                if not fgapisrv_db.user_exists(user):
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
                else:
                    params = request.get_json()
                    logging.debug("params: '%s'" % params)
                    if params is not None:
                        group_list = params.get('groups', [])
                        deleted_groups =\
                            fgapisrv_db.delete_user_groups(user, group_list)
                        if deleted_groups is not None:
                            status = 200
                            response = {'groups': deleted_groups}
                        else:
                            status = 400
                            response = {
                                'message':
                                    ('Unable to delete groups %s'
                                     ' to user \'%s\'') %
                                    (group_list, user)
                            }
                    else:
                        status = 400
                        response = {
                            'message': 'Missing groups'
                        }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/users/<user>/tasks', methods=['GET', ])
@login_required
def user_tasks(user, apiver=fg_config['fgapiver']):

    logging.debug('user_tasks(%s)/%s: %s' % (request.method,
                                             user,
                                             request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        application = request.values.get('application')
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_tasks_view")
            if auth_state is True:
                if fgapisrv_db.user_exists(user):
                    tasks_list = []
                    user_task_ids =\
                        fgapisrv_db.user_tasks_retrieve(user, application)
                    for task_id in user_task_ids:
                        task_record = fgapisrv_db.get_task_record(task_id)
                        tasks_list += [task_record, ]
                    status = 200
                    response = {'tasks': tasks_list}
                else:
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route(
    '/<apiver>/users/<user>/tasks/<task_id>', methods=['GET', ])
@login_required
def user_tasks_id(user, task_id, apiver=fg_config['fgapiver']):

    logging.debug('user_tasks(%s)/%s: %s' % (request.method,
                                             user,
                                             request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "users_tasks_view")
            if auth_state is True:
                if fgapisrv_db.user_exists(user):
                    response = fgapisrv_db.get_task_record(task_id)
                    status = 200
                else:
                    status = 404
                    response = {
                        'message': 'User \'%s\' does not exists' % user
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/users/<user>/data',
                methods=['GET', 'POST', 'DELETE', 'PATCH'])
@login_required
def users_user_data(user, apiver=fg_config['fgapiver']):

    logging.debug('user_data(%s)/%s: %s' % (request.method,
                                            user,
                                            request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            if fgapisrv_db.user_exists(user):
                data = fgapisrv_db.user_data(user)
                status = 200
                response = {'data': data}
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
                data = request.get_json()
                logging.debug("data: '%s'" % data)
                if data is not None:
                    data_entries = data.get('data', [])
                    inserted_data =\
                        fgapisrv_db.add_user_data(user, data_entries)
                    if inserted_data is not None:
                        status = 201
                        response = {'data': inserted_data}
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to add data %s '
                                 'to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        elif request.method == 'DELETE':
            if not fgapisrv_db.user_exists(user):
                status = 404
                response = {
                    'message': 'User \'%s\' does not exists' % user
                }
            else:
                data = request.get_json()
                logging.debug("data: '%s'" % data)
                if data is not None:
                    data_entries = data.get('data', [])
                    deleted_data =\
                        fgapisrv_db.delete_user_data(user, data_entries)
                    if deleted_data is not None:
                        status = 201
                        response = {'data': deleted_data}
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to delete data %s'
                                 ' to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        elif request.method == 'PATCH':
            if not fgapisrv_db.user_exists(user):
                status = 404
                response = {
                    'message': 'User \'%s\' does not exists' % user
                }
            else:
                data = request.get_json()
                logging.debug("data: '%s'" % data)
                if data is not None:
                    data_entries = data.get('data', [])
                    modified_data =\
                        fgapisrv_db.modify_user_data(user, data_entries)
                    if modified_data is not None:
                        status = 201
                        response = {'data': modified_data}
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to modify data %s'
                                 ' to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp

@ugr_apis.route('/<apiver>/users/<user>/data/<data_name>',
                methods=['GET', 'POST', 'DELETE', 'PATCH'])
@login_required
def users_user_data_name(user, data_name, apiver=fg_config['fgapiver']):

    logging.debug('user_data_name(%s, %s)/%s: %s'
                  % (request.method,
                     user,
                     data_name,
                     request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user)
        if request.method == 'GET':
            if fgapisrv_db.user_exists(user):
                data = fgapisrv_db.user_data_name(user, data_name)
                status = 200
                response = data
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
                data = request.get_json()
                data['data_name'] = data_name
                if data is not None:
                    data_entries = [data, ]
                    inserted_data =\
                        fgapisrv_db.add_user_data(user, data_entries)
                    if inserted_data is not None:
                        status = 201
                        response = inserted_data[0]
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to add data %s '
                                 'to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        elif request.method == 'DELETE':
            if not fgapisrv_db.user_exists(user):
                status = 404
                response = {
                    'message': 'User \'%s\' does not exists' % user
                }
            else:
                data = {'data_name': data_name}
                if data is not None:
                    data_entries = [data, ]
                    deleted_data =\
                        fgapisrv_db.delete_user_data(user, data_entries)
                    if deleted_data is not None:
                        status = 201
                        response = deleted_data[0]
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to delete data %s'
                                 ' to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        elif request.method == 'PATCH':
            if not fgapisrv_db.user_exists(user):
                status = 404
                response = {
                    'message': 'User \'%s\' does not exists' % user
                }
            else:
                data = request.get_json()
                data['data_name'] = data_name
                logging.debug("data: '%s'" % data)
                if data is not None:
                    data_entries = [data, ]
                    modified_data =\
                        fgapisrv_db.modify_user_data(user, data_entries)
                    if modified_data is not None:
                        status = 201
                        response = modified_data[0]
                    else:
                        status = 400
                        response = {
                            'message':
                                ('Unable to modify data %s'
                                 ' to user \'%s\'') %
                                (data_entries, user)
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing data'
                    }
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/groups', methods=['GET', 'POST'])
@login_required
def groups(apiver=fg_config['fgapiver']):

    logging.debug('groups(%s): %s' % (request.method,
                                      request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_view")
            if auth_state is True:
                group_list = fgapisrv_db.groups_retrieve()
                status = 200
                response = {'groups': group_list}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_change")
            if auth_state is True:
                params = request.get_json()
                if params is not None:
                    logging.debug("params: '%s'" % params)
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
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/groups/<group>', methods=['GET', 'POST'])
@login_required
def groups_group(group, apiver=fg_config['fgapiver']):

    logging.debug('groups_group(%s)/%s: %s' % (request.method,
                                               group,
                                               request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_view")
            if auth_state is True:
                group_info = fgapisrv_db.group_retrieve(group)
                if group_info is not None:
                    status = 200
                    response = group_info
                else:
                    status = 404
                    response = {
                        'message': 'No groups found with name or id: %s'
                                   % group}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            status = 404
            response = {"message": "Not yet implemented"}
        else:
            status = 404
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/groups/<group>/apps', methods=['GET', 'POST'])
@login_required
def groups_group_apps(group, apiver=fg_config['fgapiver']):

    logging.debug('groups_group_apps(%s)/%s: %s' % (request.method,
                                                    group,
                                                    request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_apps_view")
            if auth_state is True:
                group_apps_info = fgapisrv_db.group_apps_retrieve(group)
                if group_apps_info is not None:
                    status = 200
                    response = group_apps_info
                else:
                    status = 404
                    response = {
                        'message':
                            ('No applications found for group having name '
                             'or id: %s' % group)}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_apps_change")
            if auth_state is True:
                params = request.get_json()
                if params is not None:
                    logging.debug("params: '%s'" % params)
                    app_ids = params.get('applications', [])
                    new_ids = fgapisrv_db.group_apps_add(group, app_ids)
                    if new_ids is not []:
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
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/groups/<group>/roles', methods=['GET', 'POST'])
@login_required
def groups_group_roles(group, apiver=fg_config['fgapiver']):

    logging.debug('groups_group_roles(%s)/%s: %s' % (request.method,
                                                     group,
                                                     request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_roles_view")
            if auth_state is True:
                group_roles_info = fgapisrv_db.group_roles_retrieve(group)
                if group_roles_info is not None:
                    status = 200
                    response = group_roles_info
                else:
                    status = 404
                    response = {
                        'message': ('No roles found for group having name or '
                                    'id: %s' % group)}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        elif request.method == 'POST':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "groups_roles_change")
            if auth_state is True:
                params = request.get_json()
                if params is not None:
                    logging.debug("params: '%s'" % params)
                    role_ids = params.get('roles', [])
                    new_roles = fgapisrv_db.group_roles_add(group, role_ids)
                    if new_roles is not []:
                        status = 201
                        response = {'roles': new_roles}
                    else:
                        status = 400
                        response = {
                            'message':
                            ('Unable to add roles: \'%s\' '
                             'to the group: \'%s\'' % (role_ids,
                                                       group))
                        }
                else:
                    status = 400
                    response = {
                        'message': 'Missing group'
                    }
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@ugr_apis.route('/<apiver>/roles', methods=['GET', ])
@login_required
def roles(apiver=fg_config['fgapiver']):

    logging.debug('groups(%s): %s' % (request.method,
                                      request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        status = 400
        response = {"message": message}
    else:
        user_name = current_user.get_name()
        user_id = current_user.get_id()
        logging.debug("user_name: '%s'" % user_name)
        logging.debug("user_id: '%s'" % user_id)
        user = request.values.get('user', user_name)
        if request.method == 'GET':
            auth_state, auth_msg = \
                authorize_user(current_user, None, user, "roles_view")
            if auth_state is True:
                role_list = fgapisrv_db.roles_retrieve()
                status = 200
                response = {'roles': role_list}
            else:
                status = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
        else:
            status = 400
            response = {"message": "Unhandled method: '%s'" % request.method}
    logging.debug('message: %s' % response.get('message', 'success'))
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp
