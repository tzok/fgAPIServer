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

from flask import request
import logging.config
import socket
import uuid
from Crypto.Cipher import ARC4
from fgapiserver_config import fg_config
from fgapiserver_db import fgapisrv_db
import sys
import time
import base64
import logging


"""
  FutureGateway APIServer tools
"""

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-10-18 10:50:54'

# Logging
logger = logging.getLogger(__name__)

#
# Tooling functions commonly used by fgapiserver* source codes
#


def json_bool(bool_value):
    """
    Accepts true/false values in different forms from json streams and
    transform it in boolean value accordingly to the following table:
        bool_Value = ["true"|"True"|"TRUE]" -> True/False otherwise
        bool_Value = true/false             -> True/False (bool)
        bool_value = "1"/"0"                -> True/False (str)
        bool_value = 1/0                    -> True/False (int)
    """
    if type(bool_value) != bool:
        bool_value = str(bool_value)
        if bool_value.lower() == 'true' or bool_value == '1':
            bool_value = True
        else:
            bool_value = False
    return bool_value


def check_api_ver(apiver):
    """
    Check the API version

    Future versions of this function can be used to route different versions

    :return: A list containing three values:
              - A true boolean value if the version matches
              - 404 error code in case versions are not matching
              - The error message in case versions are not matching
    """
    logging.debug("APIVER param: %s - config: %s"
                  % (apiver, fg_config['fgapiver']))
    if apiver == fg_config['fgapiver']:
        ret_value = (True, 200, 'Supported API version %s' % apiver)
    else:
        ret_value = (False, 404, "Unsupported API version %s" % apiver)
    return ret_value


def check_db_ver():
    """
    Database version check

    :return: This function will check the database connectivity, set the
             fgapisrv_db global variable and terminate with error if the
             database schema version is not aligned with the version
             required by the code; see fgapisrv_dbver in configuration file
    """
    if fgapisrv_db is None:
        msg = "Unable to connect to the database!"
        logging.error(msg)
        print(msg)
        sys.exit(1)
    else:
        # getDBVersion
        db_ver = fgapisrv_db.get_db_version()
        if fg_config['fgapisrv_dbver'] is None or \
           fg_config['fgapisrv_dbver'] == '' or \
           fg_config['fgapisrv_dbver'] != db_ver:
            msg = ("Current database version '%s' is not compatible "
                   "with this version of the API server front-end; "
                   "version %s is required.\n"
                   "It is suggested to update your database applying "
                   "new available patches."
                   % (db_ver, fg_config['fgapisrv_dbver']))
            logging.error(msg)
            sys.exit(1)
    logging.debug("Check database version passed")
    return db_ver


def srv_uuid():
    """
    Service UUID

    :return: This function returns the service UUID calculated
             using the server' hostname
    """

    # UUID from hostname/IP
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, socket.gethostname()))


def paginate_response(response, page, per_page, page_url):
    """
    Paginate the incoming response json vector, accordinlgly to page and
    per_page values
    :param response: The whole response text
    :param page: The selected page number
    :param per_page: How many response record per page
    :param page_url: The url to get this page
    :return: The number of specified response records of the selected page
    """
    links = []
    if page is not None and per_page is not None:
        pg = int(page)
        if pg > 0:
            pg -= 1
        ppg = int(per_page)
        if pg > len(response) / ppg:
            pg = len(response) / ppg
        max_pages = int(len(response) / ppg + (1 * len(response) % ppg))
        record_from = pg * ppg
        record_to = record_from + ppg
        paginated_response = response[record_from:record_to]
        for link_page in range(0, max_pages):
            if link_page == pg:
                rel = "self"
            elif link_page < pg:
                rel = "prev"
            else:
                rel = "next"
            if "?" in page_url:
                filter_char = "&"
            else:
                filter_char = "?"
            href = "%s%spage=%s&per_page=%s" % (page_url,
                                                filter_char,
                                                link_page + 1,
                                                ppg)
            links += [{"rel": rel,
                       "href": href}, ]
    else:
        paginated_response = response
        links += [{"rel": "self",
                   "href": page_url}, ]
    return paginated_response, links


def get_task_app_id(taskid):
    """
    Return the application id associated to the given task_id
    :param taskid: Task id
    :return: The associated application id associated to the given task id
    """

    task_info = fgapisrv_db.get_task_info(taskid)
    app_record = task_info.get('application', None)
    if app_record is not None:
        logging.debug("Found app_id: '%s' for task_id: '%s'"
                      % (app_record['id'], taskid))
        return app_record['id']
    logging.warn("Could not find app_id for task_id: '%s'" % taskid)
    return None


def process_log_token(logtoken):
    """
    processLogToken retrieve username and password from a given login token

    (!)Override this method to manage more complex and secure algorithms;
       tester code uses the following encrypted string to store user
       credentials:
       username=<username>:password=<password>:timestamp=<timestamp>

    To create such log tokens, please use the following python snippet:

    from Crypto.Cipher import ARC4
    import time
    import base64
    secret = "0123456789ABCDEF" # (!) Please use fgapiserver_secret value
    username = "<username>"
    password = "<password>"
    # Encode
    obj=ARC4.new(secret)
    b64em = base64.b64encode(obj.encrypt("username=%s:password=%s:timestamp=%s"
                             % (username,password,int(time.time()))))
    print(b64em)
    # Decode
    obj=ARC4.new(secret)
    creds = obj.decrypt(base64.b64decode(b64em))
    print(creds)

    :param logtoken: The encripted string containing the:
                 username=<username>:password=<password>:timestamp=<timestamp>
                 The key is encripted using a key, see fgapisrv_secret value
                 in configuration file
                 Username and Passord credentials are stored inside in the
                 APIServer users table
    :return: Unencripted triple: (username, password, timestamp)
    """

    username = ""
    password = ""
    timestamp = 0
    obj = ARC4.new(fg_config['fgapisrv_secret'])
    token_data = obj.decrypt(base64.b64decode(logtoken))
    try:
        creds = str(token_data, 'utf-8')
    except TypeError:
        creds = str(token_data).encode('utf-8')
    credfields = creds.split(":")
    if len(credfields) > 0:
        username = credfields[0].split("=")[1]
        password = credfields[1].split("=")[1]
        timestamp = credfields[2].split("=")[1]
    logging.debug("Logtoken: '%s'\n"
                  "    User: '%s'\n"
                  "    Password: '%s'\n"
                  "    Timestamp: '%s'" % (logtoken,
                                           username,
                                           password,
                                           timestamp))
    return username, password, timestamp


def create_session_token(**kwargs):
    """
    This function accepts login tokens or directly username/password
    credentials returning an access token
    :param kwargs: logtoken - A token containing encrypted credentials
                  plus a timestamp
                  username,password - Credentials of APIServer users
    :return: An access token to be used by any further transaction with
             the APIServer front-end
    """
    timestamp = int(time.time())
    user = kwargs.get("user", "")
    logtoken = kwargs.get("logtoken", "")
    username = kwargs.get("username", "")
    password = kwargs.get("password", "")
    delegated_token = ''

    if len(logtoken) > 0:
        # Calculate credentials starting from a logtoken
        username, password, timestamp = process_log_token(logtoken)
    if len(username) > 0 and len(password) > 0:
        # Create a new access token starting from given username and password
        # (DBRequired)
        sestoken = fgapisrv_db.create_session_token(username,
                                                    password,
                                                    timestamp)
    else:
        # Nor logtoken or (username/password) provided
        return '', ''

    # Log token info
    logging.debug("Session token is:\n"
                  "logtoken: '%s'\n"
                  "username: '%s'\n"
                  "password: '%s'\n"
                  "timestamp: '%s'\n" % (sestoken,
                                         logtoken,
                                         username,
                                         password))

    # Verify is delegated user is provided
    if len(sestoken) > 0 and len(user) > 0:
        # A different user has been specified
        # First get user info from token
        user_token = fgapisrv_db.user_token(sestoken)

        # Verify the user has the user_impersonate right
        if user_token['name'] != user and\
           fgapisrv_db.verify_user_role(user_token['id'], 'user_impersonate'):
            delegated_token = fgapisrv_db.create_delegated_token(sestoken,
                                                                 user)
            logging.debug(
                "Delegated token is: '%s' for user: '%s'" %
                (delegated_token, user))

    return sestoken, delegated_token


#
# header_links; take care of _links fields and Location specified
#               inside the passed json dictionary content
#
def header_links(req, resp, json_dict):
    if '_links' in json_dict:
        for link in json_dict['_links']:
            resp.headers.add('Link', ('%s; '
                                      'rel="%s", <%s>; '
                                      % (req.url,
                                         link['rel'],
                                         link['href'])))
        resp.headers.add('Location', req.url)


#
# Not allowed method common answer
#
def not_allowed_method():
    return 400, {"message": "Method '%s' is not allowed for this endpoint"
                            % request.method}


#
# Envconfig DB config  and registry functions
#


def check_db_reg(config):
    """
    Running server registration check

    :return: This fucntion checks if this running server has been registered
             into the database. If the registration is not yet done, the
             registration will be performed and the current configuration
             registered. If the server has been registered return the
             configuration saved from the registration.
    """

    # Retrieve the service UUID
    fgapisrv_uuid = srv_uuid()
    if not fgapisrv_db.is_srv_reg(fgapisrv_uuid):
        # The service is not registered
        # Register the service and its configuration variables taken from
        # the configuration file and overwritten by environment variables
        logging.debug("Server has uuid: '%s' and it results not yet registered"
                      % fgapisrv_uuid)
        fgapisrv_db.srv_register(fgapisrv_uuid, config)
        db_state = fgapisrv_db.get_state()
        if db_state[0] != 0:
            msg = ("Unable to register service under uuid: '%s'"
                   % fgapisrv_uuid)
            logging.error(msg)
            print(msg)
            sys.exit(1)
    else:
        # Registered service checks for database configuration
        logging.debug("Service with uuid: '%s' is already registered"
                      % fgapisrv_uuid)


def update_db_config(config):
    """
        Update given configuration with registered service configuration

        :return: When this function is called the service is already registered
                 and passed configuration values are compared with database
                 settings that will have highest priority. Returned value
                 will be the setting extracted from the DB if enabled.
    """
    # Retrieve the service UUID
    fgapisrv_uuid = srv_uuid()
    db_config = fgapisrv_db.srv_config(fgapisrv_uuid)
    for key in config.keys():
        if config[key] != db_config[key]:
            logging.debug("DB configuration overload: conf(%s)='%s'<-'%s'"
                          % (key, config[key], db_config[key]))
            config[key] = db_config[key]
    return config
