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

from flask import request
import logging.config
import socket
import uuid

from Crypto.Cipher import ARC4
from fgapiserverconfig import FGApiServerConfig
from fgapiserverdb import get_db
import os
import sys
import time
import base64
import logging.config

"""
  FutureGateway APIServer tools
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
fg_config = FGApiServerConfig(fgapiserver_config_file)

# FutureGateway database object
fgapisrv_db = None

# Load configuration
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])

# Logging
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])
logger = logging.getLogger(__name__)
logger.debug("fgAPIServer is starting ...")
logger.debug(fg_config.get_messages())

#
# Tooling functions commonly used by fgapiserber_ source codes
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


def get_fgapiserver_db():
    """
    Retrieve the fgAPIServer database object instance

    :return: Return the fgAPIServer database object or None if the
             database connection fails
    """
    db, message = get_db(
        db_host=fg_config['fgapisrv_db_host'],
        db_port=fg_config['fgapisrv_db_port'],
        db_user=fg_config['fgapisrv_db_user'],
        db_pass=fg_config['fgapisrv_db_pass'],
        db_name=fg_config['fgapisrv_db_name'],
        iosandbbox_dir=fg_config['fgapisrv_iosandbox'],
        fgapiserverappid=fg_config['fgapisrv_geappid'])
    if db is None:
        logger.error(message)
    return db


def check_api_ver(apiver):
    """
    Check the API version

    Future versions of this function can be used to route different versions

    :return: A list containing three values:
              - A true boolean value if the version matches
              - 404 error code in case versions are not matching
              - The error message in case versions are not matching
    """
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
    global fgapisrv_db

    fgapisrv_db = get_fgapiserver_db()
    if fgapisrv_db is None:
        msg = "Unable to connect to the database!"
        logger.error(msg)
        print msg
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
            logger.error(msg)
            print msg
            sys.exit(1)
    logger.debug("Check database version passed")
    return db_ver


def srv_uuid():
    """
    Service UUID

    :return: This function returns the service UUID calculated
             using the server' hostname
    """

    # UUID from hostname/IP
    return uuid.uuid3(uuid.NAMESPACE_DNS, socket.gethostname())


def check_db_cfg():
    """
    Check configuration changes

    :return: This function checks configuration changes, reloading
             configuration settings in chase their values have been
             modified since last check
    """

    fgapisrv_uuid = srv_uuid()
    fg_dbconfig = fgapisrv_db.srv_config_check(fgapisrv_uuid)
    if fg_dbconfig is not None:
        fg_config.load_config(fg_dbconfig)
        logger.debug('Configuration change detected:\n%s\n' % fg_dbconfig)


def check_db_reg():
    """
    Running server registration check

    :return: This fucntion checks if this running server has been registered
             into the database. If the registration is not yet done, the
             registration will be performed and the current configuration
             registered. If the server has been registered retrieve the
             configuration saved from the registration.
    """

    # Retrieve the service UUID
    fgapisrv_uuid = srv_uuid()
    if not fgapisrv_db.is_srv_reg(fgapisrv_uuid):
        # The service is not registered
        # Register the service and its configuration variables taken from
        # the configuration file and overwritten by environment variables
        logger.debug("Server has uuid: '%s' and it results not yet registered"
                     % fgapisrv_uuid)
        fgapisrv_db.srv_register(fgapisrv_uuid, fg_config)
        db_state = fgapisrv_db.get_state()
        if db_state[0] != 0:
            msg = ("Unable to register service under uuid: '%s'"
                   % fgapisrv_uuid)
            logger.error(msg)
            print(msg)
            sys.exit(1)
    else:
        # Registered service checks for database configuration
        check_db_cfg()
    logger.debug("Check service registry passed")


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
        max_pages = len(response) / ppg + (1 * len(response) % ppg)
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
        logger.debug("Found app_id: '%s' for task_id: '%s'"
                     % (app_record['id'], taskid))
        return app_record['id']
    logger.warn("Could not find app_id for task_id: '%s'" % taskid)
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
    print b64em
    # Decode
    obj=ARC4.new(secret)
    creds = obj.decrypt(base64.b64decode(b64em))
    print creds

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
    creds = obj.decrypt(base64.b64decode(logtoken))
    credfields = creds.split(":")
    if len(credfields) > 0:
        username = credfields[0].split("=")[1]
        password = credfields[1].split("=")[1]
        timestamp = credfields[2].split("=")[1]
    logger.debug("Logtoken: '%s'\n"
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
    global fgapisrv_db
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
    logger.debug("Session token is:\n"
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
            logger.debug(
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
    return 400,\
           {"message": "Method '%s' is not allowed for this endpoint"
                       % request.method}
