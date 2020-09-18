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

import logging.config
from flask import Flask
from flask import Response
from flask import abort
from flask import request
from flask_login import LoginManager
from flask_login import login_required
from flask_login import current_user
from werkzeug.utils import secure_filename
from fgapiserver_config import FGApiServerConfig
from fgapiserverptv import FGAPIServerPTV
from fgapiserver_user import User
from fgapiserver_ugr_apis import ugr_apis
from fgapiserver_auth import authorize_user
from fgapiserver_tools import get_fgapiserver_db,\
                              json_bool,\
                              check_api_ver,\
                              check_db_ver,\
                              check_db_reg,\
                              update_db_config,\
                              paginate_response,\
                              get_task_app_id,\
                              create_session_token,\
                              header_links,\
                              not_allowed_method
import os
import sys
import json
import base64
import logging.config

"""
  FutureGateway APIServer front-end
"""

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
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

# FutureGateway database object
fgapisrv_db = get_fgapiserver_db()

# Load configuration
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])

# Logging
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])
logger = logging.getLogger(__name__)
logger.debug("fgAPIServer is starting ...")
logger.debug(fg_config.get_messages())

# setup Flask app
app = Flask(__name__)
app.register_blueprint(ugr_apis)
login_manager = LoginManager()
login_manager.init_app(app)


##
# flask-login
##

# Retrieve the session token from Header Authorization field or from token in
# the argument list
# This function verifies the session token and return the user object if the
# check is successful
# The User object holds database user id and the associated user name


@login_manager.request_loader
def load_user(req):
    logger.debug("LoadUser: begin")
    fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
    fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'
    fg_config = FGApiServerConfig(fgapiserver_config_file)
    # Login manager could be disabled in conf file
    if fg_config['fgapisrv_notoken']:
        logger.debug("LoadUser: notoken is true")
        user_info = fgapisrv_db.get_user_info_by_name(
            fg_config['fgapisrv_notokenusr'])
        user_id = user_info["id"]
        user_name = user_info["name"]
        logger.debug(("LoadUser: Session token disabled; "
                      "behaving has user: '%s' (%s)"
                      % (user_name, user_id)))
        return User(int(user_info["id"]), user_info["name"], '')

    logger.debug("LoadUser: using token")
    auth_token = req.headers.get('Authorization')
    if auth_token is None:
        auth_token = req.args.get('token')
    logger.debug("LoadUser: token is '%s'" % auth_token)

    if auth_token is not None:
        # Check for Portal Token verification  (PTV) method
        if fg_config['fgapisrv_lnkptvflag']:
            logger.debug("LoadUser: (PTV)")
            token_fields = auth_token.split()
            if token_fields[0] == "Bearer":
                try:
                    auth_token = token_fields[1]
                except IndexError:
                    logger.debug("Passed empty Bearer token")
                    return None
            elif token_fields[0] == "Task":
                # Task token management
                # Not available
                try:
                    auth_token = token_fields[1]
                    logger.debug("Task token '%s' (not yet supported)"
                                 % auth_token)
                except IndexError:
                    logger.debug("Passed empty Task token")
                    return None
                logger.debug("Task token not yet implemented")
                return None
            else:
                auth_token = token_fields[0]
            logger.debug("LoadUser: token field is '%s'" % auth_token)
            ptv = FGAPIServerPTV(endpoint=fg_config['fgapisrv_ptvendpoint'],
                                 tv_user=fg_config['fgapisrv_ptvuser'],
                                 tv_password=fg_config['fgapisrv_ptvpass'])
            result = ptv.validate_token(auth_token)
            logger.debug("LoadUser: validate_token: '%s'" % result)
            # result: valid/invalid and optionally portal username and/or
            # its group from result map the corresponding APIServer username
            # fgapisrv_ptvdefusr
            if result['portal_validate']:
                portal_user = result.get('portal_user', '')
                portal_group = result.get('portal_group', '')
                portal_groups = result.get('portal_groups', [])
                portal_subject = result.get('portal_subject', '')
                logger.debug(("LoadUser: portal_user: %s\n"
                              "portal_group: %s\n"
                              "portal_groups: %s\n"
                              "portal_subject: %s") % (portal_user,
                                                       portal_group,
                                                       portal_groups,
                                                       portal_subject))
                # Before to map users; verify that returned PTV record points
                # to an unregistered subject id (i.e. LiferayIAM).
                # When name is empty and subject value is provided, the name
                # field will be populated with the subject value and the name
                # will be registered if not present in the DB. this allows
                # not registered users to access the APIs in an isolated way
                # The Group/s field will be used to register the subject user
                # in the proper group(s) providing the correct rights
                if portal_user == '' and portal_subject is not None:
                    portal_user = portal_subject
                    # Prepare a groups vector containing group(s) associated
                    # to the PTV user. Returned PTV groups should exist in the
                    # fgAPIServer database; otherwise a default group will be
                    # associated
                    if portal_group != '':
                        portal_groups.append(portal_group)
                    fg_groups = fgapisrv_db.get_ptv_groups(portal_groups)
                    if len(fg_groups) == 0:
                        # Assign a default FG group
                        fg_groups = [fg_config['fgapisrv_ptvdefgrp']]
                    fg_user = fgapisrv_db.register_ptv_subject(portal_user,
                                                               fg_groups)
                    if fg_user != ():
                        fgapisrv_db.register_token(fg_user[0],
                                                   auth_token,
                                                   portal_subject)
                        logger.debug("LoadUser: '%s' - '%s'"
                                     % (fg_user[0], fg_user[1]))
                        logger.debug("LoadUser: (end)")
                        return User(fg_user[0], fg_user[1], auth_token)
                # Map the portal user with one of defined APIServer users
                # accordingly to the rules defined in fgapiserver_ptvmap.json
                # file. The json contains the list of possible APIServer
                # users with an associated list of possible portal users and
                # groups names that verify the mapping; below an example:
                #
                # fgapiserver_ptvmap.json: {
                #   "futuregateway":
                #        [ "group_a", ... "group_b", "user_a", "user_b", ... ]
                #   "test":
                #       [ "groupc", ... "group d", "user_c", ... "user d" .. ]
                #   "<APIServer user>":
                #      [ "<associated portal group>",
                #        "<associated portal_user>", ... ]
                # }
                #
                # If the PTV returns "user_a", "futuregateway" user will be
                # mapped, while if no mapping is available or portal_user and
                # groups are  not available a default user will be used,
                # see fgapisrv_ptvdefusr in configuration file
                logger.debug("LoadUser: Mapping user")
                mapped_userid = 0
                mapped_username = ''
                with open(fg_config['fgapisrv_ptvmapfile']) as ptvmap_file:
                    ptvmap = json.load(ptvmap_file)
                # portal_user or group must be not null
                if portal_user != '' \
                        or portal_group != '' \
                        or portal_groups != []:
                    # Scan all futuregateway users in json file
                    for user in ptvmap:
                        logger.debug(("LoadUser: Trying mapping "
                                      "for FG user: '%s'" % user))
                        # Scan the list of users and groups associated to FG
                        # users specified in the json file
                        for ptv_usrgrp in ptvmap[user]:
                            # The portal_user maps a user in the list
                            logger.debug(("LoadUser: Verifying "
                                          "portal_user='%s' "
                                          "matches user '%s'") %
                                         (portal_user, ptv_usrgrp))
                            if ptv_usrgrp == portal_user:
                                logger.debug("LoadUser: mapped user %s <- %s"
                                             % (user, portal_user))
                                mapped_username = user
                                break
                            # The portal_group maps a group in the list
                            logger.debug(("LoadUser: Verifying "
                                          "portal_group='%s' "
                                          "matches group '%s'") %
                                         (ptv_usrgrp, portal_group))
                            if ptv_usrgrp == portal_group:
                                logger.debug("LoadUser: mapped group %s <- %s"
                                             % (user, portal_group))
                                mapped_username = user
                                break
                            # The portal_groups maps a group in the list
                            logger.debug(("LoadUser: Verifying if "
                                          "portal_groups='%s' "
                                          "matches group '%s'") %
                                         (portal_groups, ptv_usrgrp))
                            group_found = ''
                            for group in portal_groups:
                                logger.debug("LoadUser: group '%s' ? '%s'" %
                                             (group, ptv_usrgrp))
                                if group == ptv_usrgrp:
                                    group_found = group
                                    break
                                else:
                                    logger.debug("  nomatch")
                            if group_found != '':
                                logger.debug("LoadUser: mapped group %s <- %s"
                                             % (user, group_found))
                                mapped_username = user
                                break
                        if mapped_username != '':
                            user_info = fgapisrv_db.get_user_info_by_name(
                                mapped_username)
                            mapped_userid = user_info["id"]
                            mapped_username = user_info["name"]
                            logger.debug(
                                "LoadUser: mapped user %s <- %s (unused)" %
                                (mapped_userid, mapped_username))
                            break
                        logger.debug(("LoadUser: PTV mapped user - "
                                      "user_rec(0): '%s',user_rec(1): '%s'")
                                     % (mapped_userid, mapped_username))
                        fgapisrv_db.register_token(mapped_userid,
                                                   auth_token,
                                                   portal_subject)
                        logger.debug("LoadUser: '%s' - '%s'" %
                                     (mapped_userid, mapped_username))
                        logger.debug("LoadUser: (end)")
                        return User(mapped_userid, mapped_username, auth_token)
                # No portal user and group are returned or no mapping
                # is available returning default user
                user_info = fgapisrv_db. \
                    get_user_info_by_name(fg_config['fgapisrv_ptvdefusr'])
                default_userid = user_info["id"]
                default_username = user_info["name"]
                logger.debug(("LoadUser: No map on portal user/group "
                              "not availabe, using default user"))
                logger.debug(("LoadUser: PTV mapped user - "
                              "user_id: '%s',user_name: '%s'"
                              % (default_userid, default_username)))
                fgapisrv_db.register_token(default_userid,
                                           auth_token,
                                           portal_subject)
                logger.debug("LoadUser: '%s' - '%s'" %
                             (default_userid, default_username))
                logger.debug("LoadUser: (end)")
                return User(default_userid, default_username, auth_token)
            else:
                logger.debug("LoadUser: PTV token '%s' is not valid"
                             % auth_token)
                return None
        else:
            logger.debug(("LoadUser: Verifying token with "
                          "baseline token management"))
            user_rec = fgapisrv_db.verify_session_token(auth_token)
            logger.debug("LoadUser: user_id: '%s',user_name: '%s'"
                         % (user_rec[0], user_rec[1]))
            if user_rec is not None and user_rec[0] is not None:
                fgapisrv_db.register_token(user_rec[0], auth_token, None)
                logger.debug("LoadUser: '%s' - '%s'"
                             % (user_rec[0], user_rec[1]))
                logger.debug("LoadUser: (end)")
                return User(user_rec[0], user_rec[1], auth_token)
            else:
                logger.debug(("LoadUser: No user is associated to "
                              "session token: '%s'" % auth_token))
                logger.debug("LoadUser: (end)")
                return None
    else:
        logger.debug("LoadUser: Unable to find session token from request")
        logger.debug("LoadUser: (end)")
    return None


##
# Auth handlers
##

# Extract token from request (Header: 'Authorization: [Bearer] <token>'
def get_request_token(auth_request):
    auth_bearer = auth_request.split(" ")
    if len(auth_bearer) > 1:
        session_token = auth_bearer[1]
    elif len(auth_bearer) > 0:
        session_token = auth_bearer[0]
    else:
        session_token = ''
    return session_token

#
# /auth; used to provide a logtoken or username/password credentials and
# receive back an access token
#
@app.route('/auth', methods=['GET', 'POST'])
@app.route('/<apiver>/auth', methods=['GET', 'POST'])
def auth(apiver=fg_config['fgapiver']):
    logger.debug('auth(%s): %s' % (request.method, request.values.to_dict()))
    session_token = ""
    delegated_token = ""
    response = {}
    user = request.values.get('user', '')
    logtoken = request.values.get('token', '')
    username = request.values.get('username', '')
    password = request.values.get('password', '')
    auth_request = request.headers.get('Authorization', '')
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        if len(logtoken) > 0:
            # Retrieve access token from an login token
            session_token, delegated_token = create_session_token(
                logtoken=logtoken,
                user=user)
        elif (len(username) > 0 and
              len(password) > 0):
            # Retrieve token from given username and password
            session_token, delegated_token = create_session_token(
                username=username,
                password=base64.b64decode(password),
                user=user)
        elif len(auth_request) > 0:
            # Extract session token from auth request (view)
            session_token = get_request_token(auth_request)
        else:
            message = "No credentials found!"
        logger.debug('session token: %s' % session_token)
    elif request.method == 'POST':
        # auth may be in the form:
        #     'Bearer LOGTOKEN'
        #     'Username/Password' or 'Username:Password'
        log_token = get_request_token(auth_request)
        auth_usrnpass_column = auth_request.split(":")
        auth_usrnpass_slash = auth_request.split("/")
        if len(session_token) > 0:
            # Retrieve access token from a login token
            session_token, delegated_token = create_session_token(
                logtoken=log_token,
                user=user)
        elif len(auth_usrnpass_column) > 1:
            session_token, delegated_token = create_session_token(
                username=auth_usrnpass_column[0],
                password=base64.b64decode(auth_usrnpass_column[1]),
                user=user)
        elif len(auth_usrnpass_slash) > 1:
            session_token, delegated_token = create_session_token(
                username=auth_usrnpass_slash[0],
                password=base64.b64decode(auth_usrnpass_slash[1]),
                user=user)
        else:
            # No credentials found
            message = "No credentials found from the request"
        logger.debug('session token: %s' % session_token)
    else:
        state, response = not_allowed_method()
    if len(delegated_token) == 0:
        message += "Delegated token not created"
        if len(session_token) == 0:
            if len(message) > 0:
                message += " "
            message += "Token not created"
    if len(session_token) > 0:
        # Provide user info from session token
        token_info = fgapisrv_db.get_token_info(session_token)
        del token_info['token']
        response = {
            "token": session_token,
            "token_info": token_info
        }
        state = 200
        if len(user) > 0:
            if len(delegated_token) > 0:
                response['delegated_token'] = delegated_token
            else:
                response['message'] = (
                    "Delegated token for user '%s' not created" % user)
                state = 203
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/auth"}, ]
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


##
# Routes as specified for APIServer at http://docs.csgfapis.apiary.io
##

#
# / path; used retrieve informative or service healty information
#


@app.route('/')
@app.route('/<apiver>/')
def index(apiver=fg_config['fgapiver']):

    logger.debug('index(%s): %s' % (request.method, request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    else:
        versions = ({"id": apiver,
                     "_links": ({"rel": "self",
                                 "href": apiver},),
                     "media-types": ({"type": "application/json"}),
                     "status": __status__,
                     "updated": __update__,
                     "build:": __version__},)
        response = {
            "versions": versions,
            "config": fg_config,
            "srv_uuid": fgapiserver_uuid,
            "_links": ({"rel": "self",
                        "href": "/"},)
        }
        state = 200
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


##
# Token handlers
##

# token - used to extract token info
#
# GET - View token associated info


@app.route('/<apiver>/token', methods=['GET', ])
@login_required
def token(apiver=fg_config['fgapiver']):
    global fgapisrv_db
    global logger
    logger.debug('token(%s): %s' % (request.method, request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user_token = current_user.get_token()
    logger.debug("user_name: '%s'" % user_name)
    logger.debug("user_id: '%s'" % user_id)
    logger.debug("user_token: '%s'" % user_token)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        state = 200
        if len(user_token) == 0:
            response = {'user_id': user_id,
                        'user_name': user_name,
                        'creation': None,
                        'expiry': None,
                        'valid': True,
                        'lasting': None}
        else:
            response = fgapisrv_db.get_token_info(user_token)
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


##
# Task handlers
##

# tasks - used to view o create a new task
#
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution


@app.route('/<apiver>/tasks', methods=['GET', 'POST'])
@login_required
def tasks(apiver=fg_config['fgapiver']):

    logger.debug('tasks(%s): %s' % (request.method, request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    logger.debug("user_name: '%s'" % user_name)
    logger.debug("user_id: '%s'" % user_id)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    status = request.values.get('status', None)
    user = request.values.get('user', user_name)
    appid = request.values.get('application')
    response = {}
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "task_view")
        logger.debug("[task_view]: auth_state: '%s', auth_msg: '%s'"
                     % (auth_state, auth_msg))
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Show the whole task list
            # Before call user list check if * means ALL users or group
            # restricted users (@)
            user_impersonate = fgapisrv_db.verify_user_role(
                user_id, 'user_impersonate')
            logger.debug("user_impersonate: '%s'" % user_impersonate)
            group_impersonate = fgapisrv_db.same_group(
                user_name, user) and fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
            logger.debug("group_impersonate: '%s'" % group_impersonate)
            if user == "*" \
                    and user_impersonate is False \
                    and group_impersonate is True:
                user = "@"  # Restrict tasks only to group members
            # Add the usernname info in case of * or @ filters
            if user == "*" or user == "@":
                user = user + user_name
            # call to get tasks list
            task_list = fgapisrv_db.get_task_list(user, appid)
            logger.debug("task_list: '%s'" % task_list)
            # Prepare response
            task_array = []
            for taskid in task_list:
                task_record = fgapisrv_db.get_task_record(taskid)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # DBError getting TaskRecord
                    # Prepare for 403
                    state = 403
                    response = {
                        "message": db_state[1]
                    }
                    break
                else:
                    if status is None or task_record['status'] == status:
                        task_record['_links'] = [
                            {"rel": "self",
                             "href": "/%s/tasks/%s" % (apiver, taskid)},
                            {"rel": "input",
                             "href": "/%s/tasks/%s/input" % (apiver, taskid)}]
                        task_array += [task_record, ]
            if state != 403:
                state = 200
                paged_tasks, paged_links =\
                    paginate_response(
                        task_array,
                        page,
                        per_page,
                        request.url)
                response = {"tasks": paged_tasks,
                            "_links": paged_links}
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_run")
        logger.debug("[app_run]: auth_state: '%s', auth_msg: '%s'"
                     % (auth_state, auth_msg))
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            logger.debug("params: '%s'" % params)
            if params is not None:
                appid = params.get('application', '')
                app_desc = params.get('description', '')
                app_args = params.get('arguments', [])
                app_inpf = params.get('input_files', [])
                app_outf = params.get('output_files', [])
                # Create task
                taskid = fgapisrv_db.init_task(
                    appid, app_desc, user, app_args, app_inpf, app_outf)
                logger.debug("task_id: '%s'" % taskid)
                if taskid < 0:
                    db_state = fgapisrv_db.get_state()
                    # Error initializing task
                    # Prepare for 410 error
                    state = 410
                    response = {
                        'message': db_state[1]
                    }
                else:
                    # Prepare response
                    state = 200
                    task_record = fgapisrv_db.get_task_record(taskid)
                    response = {
                        "id": task_record['id'],
                        "application": task_record['application'],
                        "description": task_record['description'],
                        "arguments": task_record['arguments'],
                        "input_files": task_record['input_files'],
                        "output_files": task_record['output_files'],
                        "status": task_record['status'],
                        "user": task_record['user'],
                        "date": str(
                            task_record['last_change']),
                        "_links": [
                            {
                                "rel": "self",
                                "href": "/%s/tasks/%s" %
                                        (apiver,
                                         taskid)},
                            {
                                "rel": "input",
                                "href": "/%s/tasks/%s/input" %
                                        (apiver,
                                         taskid)}]}
            else:
                state = 404
                response = {
                    "message": ("Did not find any application description "
                                "json input")}
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)

@app.route(
    '/<apiver>/tasks/<taskid>',
    methods=[
        'GET',
        'PUT',
        'POST',
        'DELETE',
        'PATCH'])
@login_required
def task_id(apiver=fg_config['fgapiver'], taskid=None):
    logger.debug("tasks(%s)/%s: %s" % (request.method,
                                       taskid,
                                       request.values.to_dict()))
    user_name = current_user.get_name()
    userid = current_user.get_id()
    appid = get_task_app_id(taskid)
    user = request.values.get('user', user_name)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "task_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # User should be able to see the given app_id
            if not fgapisrv_db.task_exists(taskid, userid, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % taskid
                }
            else:
                # Get task details
                response = fgapisrv_db.get_task_record(taskid)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    state = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    # Add links_
                    response['_links'] = [
                        {
                            "rel": "input",
                            "href": "/%s/tasks/%s/input" %
                                    (apiver,
                                     taskid)}, ]
                    state = 200
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "task_delete")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.task_exists(taskid, userid, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % taskid
                }
            elif not fgapisrv_db.delete(taskid):
                state = 410
                response = {
                    "message": "Unable to delete task with id: %s" % taskid
                }
            else:
                state = 204
                response = {
                    "message": "Successfully removed task with id: %s" %
                               taskid}
                # 204 - NO CONTENT cause no output
                logger.debug(response['message'])
    elif request.method == 'PATCH':
        # PATCH on tasks accepts status change or on runtime_data
        params = request.get_json()
        new_status = params.get('status', None)
        if new_status is not None:
            # status change:
            auth_state, auth_msg = authorize_user(
                current_user, appid, user, "task_statuschange")
            if not auth_state:
                state = 402
                response = {
                    "message": "Not authorized to perform status change "
                               "request:\n%s" %
                               auth_msg}
            else:
                if not fgapisrv_db.task_exists(taskid, userid, user):
                    state = 404
                    response = {
                        "message": "Unable to find task with id: %s" % taskid
                    }
                elif not fgapisrv_db.status_change(taskid, new_status):
                    state = 410
                    response = {
                        "message": ("Unable to change status for task having "
                                    "id: %s" % taskid)
                    }
                else:
                    state = 200
                    response = {
                        "message": "Successfully changed status of task with"
                                   " id: %s" % taskid
                    }
        else:
            # runtime_data:
            #
            # The input consists in a json having the form
            # { "runtime_data" : [
            #   { "data_name":  "name"
            #    ,"data_value": "value"
            #    ,"data_desc": "description of the value"
            #    ,"data_type": "how client receives the file"
            #    ,"data_proto": "protocol used to access data"
            #   }, ... ] }
            #
            # The insertion policy will be:
            #  1) data_name does not exists, a new record will be created in
            #     runtime_data table
            #  2) data_name exists the new value will be updated to the
            #     existing name
            #
            auth_state, auth_msg = authorize_user(
                current_user, appid, user, "task_userdata")
            if not auth_state:
                state = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
            else:
                runtime_data = params.get('runtime_data', [])
                if not fgapisrv_db.task_exists(taskid, userid, user):
                    state = 404
                    response = {
                        "message": "Unable to find task with id: %s" % taskid
                    }
                elif not fgapisrv_db.patch_task(taskid, runtime_data):
                    state = 410
                    response = {
                        "message": ("Unable store runtime data for task "
                                    "having id: %s" % taskid)
                    }
                else:
                    state = 200
                    response = {
                        "message": "Successfully patched task with id: %s" %
                                   taskid}
    elif (request.method == 'PUT' or
          request.method == 'POST'):
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This finalizes the task request allowing to submit the task
# GET  - shows input files
# POST - specify input files


@app.route('/<apiver>/tasks/<taskid>/input',
           methods=['GET',
                    'POST'])
@login_required
def task_id_input(apiver=fg_config['fgapiver'], taskid=None):
    logger.debug('task_id_input(%s): %s' % (request.method,
                                            request.values.to_dict()))
    user_name = current_user.get_name()
    userid = current_user.get_id()
    appid = get_task_app_id(taskid)
    user = request.values.get('user', user_name)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "task_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Display task_input_file details
            if not fgapisrv_db.task_exists(taskid, userid, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % taskid
                }
            else:
                state = 200
                response = fgapisrv_db.get_task_record(taskid)[
                    'input_files']
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_run")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # First determine IO Sandbox location for this task
            if not fgapisrv_db.task_exists(taskid, userid, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % taskid
                }
            elif fgapisrv_db.get_task_record(taskid)['status'] != 'WAITING':
                state = 404
                response = {
                    "message": ("Task with id: %s, "
                                "is no more waiting for inputs") % taskid
                }
            else:
                task_sandbox = fgapisrv_db.get_task_io_sandbox(taskid)
                if task_sandbox is None:
                    state = 404
                    response = {
                        "message": 'Could not find IO Sandbox dir for task: %s'
                                   % taskid}
                else:
                    # Process default application files
                    fgapisrv_db.setup_default_inputs(taskid, task_sandbox)
                    # Now process files to upload
                    uploaded_files = request.files.getlist('file[]')
                    file_list = ()
                    for f in uploaded_files:
                        filename = secure_filename(f.filename)
                        f.save(os.path.join(task_sandbox, filename))
                        fgapisrv_db.update_input_sandbox_file(
                            taskid, filename, os.path.join(task_sandbox))
                        file_list += (filename,)
                    # Now get input_sandbox status
                    if fgapisrv_db.is_input_sandbox_ready(taskid):
                        # The input_sandbox is completed; trigger the GE for
                        # this task
                        if fgapisrv_db.submit_task(taskid):
                            state = 200
                            response = {
                                "task": taskid,
                                "files": file_list,
                                "message": "uploaded",
                                "gestatus": "triggered",
                                "_links": [{"rel": "task",
                                            "href": "/%s/tasks/%s" %
                                                    (apiver, taskid)}, ]}
                        else:
                            state = 412
                            response = {
                                "message": fgapisrv_db.get_state()[1]
                            }
                    else:
                        state = 200
                        response = {
                            "task": taskid,
                            "files": file_list,
                            "message": "uploaded",
                            "gestatus": "waiting"}
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# Callback mechanism for takss
# Some infrastructures provide a callback mechanism describing the status
# of the task acrivity


@app.route('/<apiver>/callback/<task_id>', methods=['GET', 'POST'])
def task_callback(apiver=fg_config['fgapiver'], taskid=None):
    global fgapisrv_db
    global logger
    logger.debug('callback(%s)/%s: %s' % (request.method,
                                          taskid,
                                          request.values.to_dict()))
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'POST':
        # Getting values
        callback_info = request.get_json()
        logger.debug("Callback info for task_id: %s - '%s'"
                     % (taskid, callback_info))
        # 204 - NO CONTENT cause no output
        state = 204
        fgapisrv_db.serve_callback(taskid, callback_info)
        response = {"message": "Callback for taks: %s" % taskid}
    else:
        state, response = not_allowed_method()
    logger.debug(response['message'])
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# File download endpoint


@app.route('/<apiver>/file', methods=['GET', ])
@login_required
def getfile(apiver=fg_config['fgapiver']):
    logger.debug('file(%s): %s' % (request.method, request.values.to_dict()))
    serve_file = None
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    file_path = request.values.get('path', None)
    file_name = request.values.get('name', None)
    taskid = fgapisrv_db.get_file_task_id(file_name, file_path)
    if taskid is not None:
        appid = get_task_app_id(taskid)
    else:
        appid = fgapisrv_db.get_file_app_id(file_path, file_name)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        if appid is None:
            auth_state = False
            auth_msg = 'Unexisting file: %s/%s' % (file_path, file_name)
        else:
            auth_state, auth_msg = authorize_user(
                current_user, appid, user, "app_run")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request: %s (%s)" %
                           (auth_msg, user_id)}
        else:
            try:
                serve_file = open('%s/%s' % (file_path, file_name), 'rb')
                serve_file_content = serve_file.read()
                resp = Response(serve_file_content, status=200)
                resp.headers['Content-type'] = 'application/octet-stream'
                resp.headers.add('Content-Disposition',
                                 'attachment; filename="%s"' % file_name)
                return resp
            except IOError as e:
                response = {
                    "message": "Unable to get file: %s/%s\n%s" %
                               (file_path, file_name, e)}
                state = 404
            finally:
                if serve_file is not None:
                    serve_file.close()
    else:
        status, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state)
    resp.headers['Content-type'] = 'application/json'
    return resp


#
# APPLICATION
#

# application - used to view o create a new application
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution


@app.route('/<apiver>/applications',
           methods=['GET',
                    'PUT',
                    'POST'])
@login_required
def applications(apiver=fg_config['fgapiver']):
    logger.debug('applications(%s): %s' % (request.method,
                                           request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    appid = None
    user = request.values.get('user', user_name)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    response = {}
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s (%s)" %
                           (auth_msg, user_id)}
        else:
            # Show the whole task list
            # call to get tasks
            app_list = fgapisrv_db.get_app_list()
            # Remove special app_id = 0 (Unassigned infrastructure)
            if 0 in app_list:
                app_list.remove(0)
            db_state = fgapisrv_db.get_state()
            if db_state[0] != 0:
                # DBError getting TaskList
                # Prepare for 402
                state = 402
                response = {
                    "message": db_state[1]
                }
            else:
                apps = []
                state = 200
                for appid in app_list:
                    app_record = fgapisrv_db.get_app_record(appid)
                    db_state = fgapisrv_db.get_state()
                    if db_state[0] != 0:
                        # DBError getting TaskRecord
                        # Prepare for 403
                        state = 403
                        response = {
                            "message": db_state[1]
                        }
                        break
                    else:
                        apps += [
                            {
                                "id":
                                    app_record['id'],
                                "name":
                                    app_record['name'],
                                "description":
                                    app_record['description'],
                                "outcome":
                                    app_record['outcome'],
                                "enabled":
                                    app_record['enabled'],
                                "parameters":
                                    app_record['parameters'],
                                "files":
                                    app_record['files'],
                                "infrastructures":
                                    app_record['infrastructures'],
                                "_links": [{"rel": "self",
                                            "href": "/%s/applications/%s"
                                                    % (apiver, appid)},
                                           {"rel": "input",
                                            "href": "/%s/applications/%s/input"
                                                    % (apiver, appid)}]
                            },
                        ]
                if response == {}:
                    paged_apps, paged_links = paginate_response(
                        apps,
                        page,
                        per_page,
                        request.url)
                    response = {"applications": paged_apps,
                                "_links": paged_links}
    elif request.method == 'PUT':
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_install")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            name = params.get('name', '')
            description = params.get('description', '')
            outcome = params.get('outcome', 'JOB')
            enabled = json_bool(params.get('enabled', False))
            parameters = params.get('parameters', [])
            inp_files = params.get('input_files', [])
            files = params.get('files', [])
            infras = params.get('infrastructures', [])
            # Create app
            appid = fgapisrv_db.init_app(
                name,
                description,
                outcome,
                enabled,
                parameters,
                inp_files,
                files,
                infras)
            if appid <= 0:
                db_state = fgapisrv_db.get_state()
                # Error initializing task
                # Prepare for 410 error
                state = 410
                response = {
                    "message": db_state[1]
                }
            else:
                # Enable the groups owned by the installing user to
                # execute the app
                fgapisrv_db.enable_app_by_userid(
                    user_id,
                    appid)
                # Prepare response
                state = 201
                app_record = fgapisrv_db.get_app_record(appid)
                response = {
                    "id": app_record['id'],
                    "name": app_record['name'],
                    "description": app_record['description'],
                    "enabled": app_record['enabled'],
                    "parameters": app_record['parameters'],
                    "files": app_record['files'],
                    "infrastructures": app_record['infrastructures'],
                    "_links": [{"rel": "input",
                                "href": "/%s/application/%s/input"
                                        % (apiver, appid)}, ]}
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)


@app.route(
    '/<apiver>/applications/<appid>',
    methods=[
        'GET',
        'DELETE',
        'PUT',
        'POST'])
@login_required
def app_id(apiver=fg_config['fgapiver'], appid=None):
    logger.debug('application(%s)/%s: %s' % (request.method,
                                             appid,
                                             request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s (%s)" %
                           (auth_msg, user_id)}
        else:
            if not fgapisrv_db.app_exists(appid):
                state = 404
                response = {
                    "message":
                        "Unable to find application with id: %s"
                        % appid}
            else:
                # Get application details
                response = fgapisrv_db.get_app_record(appid)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get AppRecord
                    # Prepare for 404 not found
                    state = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    response['_links'] = [
                        {"rel": "self",
                         "href": "/%s/application/%s/input"
                                 % (apiver, appid)}, ]
                    state = 200
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_delete")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.app_exists(appid):
                state = 404
                response = {
                    "message": "Unable to find application with id: %s" %
                               appid}
            elif not fgapisrv_db.app_delete(appid):
                state = 410
                response = {
                    "message": ("Unable to delete application with id: %s; "
                                "reason: '%s'"
                                % (appid, fgapisrv_db.get_state()[1]))}
            else:
                state = 204
                response = {
                    "message": "Successfully removed application with id: %s" %
                               appid}
                # 204 - NO CONTENT cause no output
                logger.debug(response['message'])
    elif request.method == 'POST':
        state = 404
        response = {
            "message": "Not supported method"
        }
    elif request.method == 'PUT':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_change")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            app_desc = request.get_json()
            if app_desc.get("id", None) is not None \
                    and int(app_desc['id']) != int(appid):
                state = 403
                response = {
                    "message": "JSON application id %s is different than "
                               "URL application id: %s" % (app_desc['id'],
                                                           appid)}
            elif not fgapisrv_db.app_exists(appid):
                state = 404
                response = {
                    "message": "Unable to find application with id: %s" %
                               appid}
            elif not fgapisrv_db.app_change(appid, app_desc):
                state = 410
                response = {
                    "message": ("Unable to change application with id: %s; "
                                "reason: '%s'"
                                % (appid, fgapisrv_db.get_state()[1]))}
            else:
                state = 200
                response = {
                    "message": "Successfully changed application with id: %s" %
                               appid}
    else:
        status, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


@app.route('/<apiver>/applications/<appid>/input',
           methods=['GET', 'POST'])
@login_required
def app_id_input(apiver=fg_config['fgapiver'], appid=None):
    logger.debug('index(%s)/%s/input: %s' % (request.method,
                                             appid,
                                             request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    response = {}
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s (%s)" %
                           (auth_msg, user_id)}
        else:
            # Display app_input_file details
            if not fgapisrv_db.app_exists(appid):
                state = 404
                response = {
                    "message": ("Unable to find application with id: %s"
                                % appid)
                }
            else:
                state = 200
                response =\
                    fgapisrv_db.get_app_record(appid)['files']
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "app_install")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # First determine IO Sandbox location for this task
            if not fgapisrv_db.app_exists(appid):
                state = 404
                response = {
                    "message": ("Unable to find application with id: %s"
                                % task_id)
                }
            else:
                # Now process files to upload
                app_dir = 'apps/%s' % appid
                uploaded_files = request.files.getlist('file[]')
                try:
                    os.stat(app_dir)
                    logger.debug("App dir: '%s' exists" % app_dir)
                except OSError:
                    logger.debug("Creating app dir: '%s'" % app_dir)
                    try:
                        os.makedirs(app_dir)
                    except OSError as e:
                        os.error(
                            "Error creating application directory '%s'\n%s" %
                            (app_dir, e))
                        state = 404
                        response = {"message": ("Unable to create application "
                                                "directory '%s'" % app_dir)}
                if state != 404:
                    file_list = ()
                    logger.debug("uploading file(s):")
                    for f in uploaded_files:
                        filename = secure_filename(f.filename)
                        logger.debug(" File: '%s' -> Dir: '%s'"
                                     % (filename, app_dir))
                        f.save(os.path.join(app_dir, filename))
                        fgapisrv_db.insert_or_update_app_file(appid,
                                                              filename,
                                                              app_dir)
                        file_list += (filename,)
                    state = 200
                    response = {
                        "application": appid,
                        "files": file_list,
                        "message": "uploaded successfully"}
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


#
# INFRASTRUCTURE
#


@app.route('/<apiver>/infrastructures',
           methods=['GET',
                    'PUT',
                    'POST'])
@login_required
def infrastructures(apiver=fg_config['fgapiver']):
    logger.debug('infrastructures(%s): %s' % (request.method,
                                              request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    infraid = None
    user = request.values.get('user', user_name)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    response = {}
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, infraid, user, "infra_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s (%s)" %
                           (auth_msg, user_id)}
        else:
            # Show the whole infra list
            # call to get infrastructures
            infra_list = fgapisrv_db.get_infra_list(None)
            db_state = fgapisrv_db.get_state()
            if db_state[0] != 0:
                # DBError getting InfraList
                # Prepare for 402
                state = 402
                response = {
                    "message": db_state[1]
                }
            else:
                # Prepare response
                infras = []
                state = 200
                for infraid in infra_list:
                    infra_record = fgapisrv_db.get_infra_record(infraid)
                    db_state = fgapisrv_db.get_state()
                    if db_state[0] != 0:
                        # DBError getting InfraRecord
                        # Prepare for 403
                        state = 403
                        response = {
                            "message": db_state[1]
                        }
                        break
                    else:
                        infras += [
                            {
                                "id":
                                    infra_record['id'],
                                "name":
                                    infra_record['name'],
                                "description":
                                    infra_record['description'],
                                "date":
                                    infra_record['creation'],
                                "enabled":
                                    infra_record['enabled'],
                                "virtual":
                                    infra_record['virtual'],
                                "_links": [
                                    {"rel": "self",
                                     "href": "/%s/infrastructures/%s"
                                             % (apiver, infraid)}]
                            },
                        ]
                if response == {}:
                    paged_infras, paged_links = paginate_response(
                        infras,
                        page,
                        per_page,
                        request.url)
                    response = {
                        "infrastructures": paged_infras,
                        "_links": paged_links}
    elif request.method == 'PUT':
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(current_user,
                                              None,
                                              user,
                                              "infra_add")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            name = params.get('name', '')
            description = params.get('description', '')
            enabled = params.get('enabled', True)
            vinfra = params.get('virtual', False)
            infrastructure_parameters = \
                params.get('parameters', '')
            # Create infrastructure
            infraid = fgapisrv_db.init_infra(
                name,
                description,
                enabled,
                vinfra,
                infrastructure_parameters)
            if infraid < 0:
                init_state = fgapisrv_db.get_state()
                # Error initializing infrastructure
                # Prepare for 410 error
                state = 410
                response = {
                    "message": init_state[1]
                }
            else:
                # Prepare response
                state = 201
                infra_record = fgapisrv_db.get_infra_record(infraid)
                response = {
                    "id": infra_record['id'],
                    "name": infra_record['name'],
                    "description": infra_record['description'],
                    "date": infra_record['creation'],
                    "enabled": infra_record['enabled'],
                    "virtual": infra_record['virtual'],
                    "_links": [
                        {
                            "rel": "self",
                            "href": "/%s/infrastructure/%s" %
                                    (apiver,
                                     infra_record['id'])}]}
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)


@app.route(
    '/<apiver>/infrastructures/<infraid>',
    methods=[
        'GET',
        'DELETE',
        'POST',
        'PUT'])
@login_required
def infra_id(apiver=fg_config['fgapiver'], infraid=None):
    logger.debug('infrastructures(%s)/%s: %s' % (request.method,
                                                 infraid,
                                                 request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    api_support, state, message = check_api_ver(apiver)
    if not api_support:
        response = {"message": message}
    elif request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, None, user, "infra_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s (%s)" %
                           (auth_msg, user_id)}
        else:
            if not fgapisrv_db.infra_exists(infraid):
                state = 404
                response = {
                    "message": ("Unable to find infrastructure with id: %s"
                                % infraid)}
            else:
                # Get task details
                infra_record = fgapisrv_db.get_infra_record(infraid)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    state = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    state = 200
                    response = {"id": infra_record['id'],
                                "name": infra_record['name'],
                                "description": infra_record['description'],
                                "date": infra_record['creation'],
                                "enabled": infra_record['enabled'],
                                "virtual": infra_record['virtual'],
                                "parameters": infra_record['parameters'],
                                "_links": [
                                    {"rel": "self",
                                     "href": ("/%s/infrastructure/%s"
                                              % (apiver,
                                                 infra_record['id']))}]}
    elif request.method == 'DELETE':
        appid = request.values.get('app_id', None)
        app_orphan = request.values.get('app_orphan', None)
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "infra_delete")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.infra_exists(infraid):
                state = 404
                response = {
                    "message": "Unable to find infrastructure with id: %s" %
                               infraid}
            elif not fgapisrv_db.infra_delete(infraid, appid, app_orphan):
                state = 410
                response = {
                    "message": ("Unable to delete infrastructure with id: %s; "
                                "reason: '%s'"
                                % (infraid, fgapisrv_db.get_state()[1]))}
            else:
                state = 200
                response = {
                    "message":
                        "Successfully removed infrastructure with id: %s" %
                        infraid}
    elif request.method == 'POST':
        state = 404
        response = {
            "message": "Not supported method"
        }
    elif request.method == 'PUT':
        appid = request.values.get('app_id', None)
        auth_state, auth_msg = authorize_user(
            current_user, appid, user, "infra_change")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            infra_desc = request.get_json()
            if infra_desc.get("id", None) is not None \
                    and int(infra_desc['id']) != int(infraid):
                state = 403
                response = {
                    "message": "JSON infrastructure id %s is different than "
                               "URL infrastructure id: %s" % (infra_desc['id'],
                                                              infraid)}
            elif not fgapisrv_db.infra_exists(infraid):
                state = 404
                response = {
                    "message": "Unable to find infrastructure with id: %s" %
                               infraid}
            elif not fgapisrv_db.infra_change(infraid, infra_desc):
                state = 400
                response = {
                    "message": ("Unable to change application with id: %s; "
                                "reason: '%s'"
                                % (appid, fgapisrv_db.get_state()[1]))}
            else:
                state = 200
                response = {
                    "message":
                        "Infrastructure changed correctly"
                }
    else:
        state, response = not_allowed_method()
    js = json.dumps(response, indent=fg_config['fgjson_indent'])
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
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


# IP Filtering
filtered_ips = ('193.206.190.155', )


# Common check for requests
@app.before_request
def limit_remote_addr():
    global fg_config
    # Block blacklisted IPs
    if request.remote_addr in filtered_ips:
        abort(403)  # Forbidden
    # Override configuration settings from the database
    fg_config = update_db_config(fg_config)


#
# The fgAPIServer app starts here
#


# Get database object and check the DB
check_db_ver()

# Server registration and configuration from fgdb
fgapiserver_uuid = check_db_reg(fg_config)

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    # Inform user about server activity
    print("fgAPIServer running in stand-alone mode ...")

    # Starting-up server
    if len(fg_config['fgapisrv_crt']) > 0 and \
            len(fg_config['fgapisrv_key']) > 0:
        context = (fg_config['fgapisrv_crt'],
                   fg_config['fgapisrv_key'])
        app.run(host=fg_config['fgapisrv_host'],
                port=fg_config['fgapisrv_port'],
                ssl_context=context,
                debug=fg_config['fgapisrv_debug'])
    else:
        app.run(host=fg_config['fgapisrv_host'],
                port=fg_config['fgapisrv_port'],
                debug=fg_config['fgapisrv_debug'])
