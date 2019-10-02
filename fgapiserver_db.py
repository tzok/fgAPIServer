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

import mysql.connector
import uuid
import os
import sys
import urllib
import shutil
import logging
import json
import time
from fgapiserver_config import FGApiServerConfig

"""
  GridEngine API Server database
"""
__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-03-19 11:47:47'

"""
 Database connection default settings
"""
def_db_host = 'localhost'
def_db_port = 3306
def_db_user = 'fgapiserver'
def_db_pass = 'fgapiserver_password'
def_db_name = 'fgapiserver'

"""
 Task sandboxing will be placed here Sandbox directories
 will be generated as UUID names generated during task creation
"""
def_iosandbbox_dir = '/tmp'
def_geapiserverappid = '10000'  # GridEngine sees API server as an application

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config = FGApiServerConfig(fgapiserver_config_file)

# Logging
logging.config.fileConfig(fg_config['fgapisrv_logcfg'])


def get_db(**kwargs):
    """
    Retrieve the fgAPIServer database object

    :return: Return the fgAPIServer database object or None if the
             database connection fails
    """
    args = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            args[key] = value
    db_host = args.get('db_host', def_db_host)
    db_port = args.get('db_port', def_db_port)
    db_user = args.get('db_user', def_db_user)
    db_pass = args.get('db_pass', def_db_pass)
    db_name = args.get('db_name', def_db_name)
    io_sbox = args.get('iosandbbox_dir', def_iosandbbox_dir)
    ge_apid = args.get('iosandbbox_dir', def_geapiserverappid)
    fgapiserver_db = FGAPIServerDB(
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_pass=db_pass,
        db_name=db_name,
        iosandbbox_dir=io_sbox,
        fgapiserverappid=ge_apid)
    db_state = fgapiserver_db.get_state()
    if db_state[0] != 0:
        message = ("Unbable to connect to the database:\n"
                   "  host: %s\n"
                   "  port: %s\n"
                   "  user: %s\n"
                   "  pass: %s\n"
                   "  name: %s\n"
                   % (db_host,
                      db_port,
                      db_user,
                      db_pass,
                      db_name))
        return None, message
    return fgapiserver_db, None


"""
  fgapiserver_db Class contain any call interacting with fgapiserver database
"""


class FGAPIServerDB:
    """
     API Server Database connection settings
    """
    db_host = None
    db_port = None
    db_user = None
    db_pass = None
    db_name = None
    iosandbbox_dir = def_iosandbbox_dir
    geapiserverappid = def_geapiserverappid

    """
        Error Flag and messages filled up upon failures
    """
    err_flag = False
    err_msg = ''
    message = ''

    """
        Date format
    """
    date_format_str = "%Y-%m-%dT%TZ"

    """
        date_format - convert a given datetime.datetime object into a
                      formatted datetime string
    """
    def date_format(self, datetime_var):
        return datetime_var.strftime(self.date_format_str)

    """
      FGAPIServerDB - Constructor may override default
                      values defined at the top of the file
    """

    def __init__(self, **kwargs):
        """

        :rtype:
        """
        self.db_host = kwargs.get('db_host', def_db_host)
        self.db_port = kwargs.get('db_port', def_db_port)
        self.db_user = kwargs.get('db_user', def_db_user)
        self.db_pass = kwargs.get('db_pass', def_db_pass)
        self.db_name = kwargs.get('db_name', def_db_name)
        self.iosandbbox_dir = kwargs.get('iosandbbox_dir', def_iosandbbox_dir)
        self.geapiserverappid = kwargs.get(
            'geapiserverappid', def_geapiserverappid)
        logging.debug("[DB settings]\n"
                      " host: '%s'\n"
                      " port: '%s'\n"
                      " user: '%s'\n"
                      " pass: '%s'\n"
                      " name: '%s'\n"
                      " iosandbox_dir: '%s'\n"
                      " geapiserverappid: '%s'\n"
                      % (self.db_host,
                         self.db_port,
                         self.db_user,
                         self.db_pass,
                         self.db_name,
                         self.iosandbbox_dir,
                         self.geapiserverappid))

    """
       catchDBError - common operations performed upon database
                      query/transaction failure
     """

    def catch_db_error(self, e, db, rollback):
        logging.error("[ERROR] %d: %s" % (e.args[0], e.args[1]))
        if rollback is True:
            db.rollback()
        self.err_flag = True
        self.err_msg = "[ERROR] %d: %s" % (e.args[0], e.args[1])

    """
      close_db - common operatoins performed closing DB query/transaction
    """

    @staticmethod
    def close_db(db, cursor, commit):
        if cursor is not None:
            cursor.close()
        if db is not None:
            if commit is True:
                db.commit()
            db.close()

    """
      query_done - reset the query error flag and eventually set
                   a given query related message
    """

    def query_done(self, message):
        self.err_flag = False
        self.err_msg = message
        logging.debug("Query done message:\n"
                      "%s" % message)

    """
      connect Connects to the fgapiserver database
    """

    def connect(self, safe_transaction=False):
        db = None
        while db is None:
            try:
                db = mysql.connector.connect(
                    host=self.db_host,
                    user=self.db_user,
                    passwd=self.db_pass,
                    db=self.db_name,
                    port=self.db_port)
            except:
                logging.error(
                    'Failed to connect to database. Will retry in 5 seconds')
                time.sleep(5)

        if safe_transaction is True:
            sql = "BEGIN"
            sql_data = ()
            cursor = db.cursor()
            logging.debug(sql % sql_data)
            cursor.execute(sql)
            cursor.close()
        return db

    """
     test - DB connection tester function
    """

    def test(self):
        db = None
        cursor = None
        safe_transaction = False
        try:
            # Connect the DB
            db = self.connect(safe_transaction)
            # Prepare SQL statement
            sql = "SELECT VERSION()"
            # Prepare SQL data for statement
            sql_data = ()
            # Prepare a cursor object
            cursor = db.cursor()
            # View query in logs
            logging.debug(sql % sql_data)
            # Execute SQL statement
            cursor.execute(sql)
            # Fetch a single row using fetchone() method.
            data = cursor.fetchone()
            self.query_done("Database version : '%s'" % data[0])
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)

    """
      get_db_version - Return the database version
    """

    def get_db_version(self):
        db = None
        cursor = None
        safe_transaction = False
        dbver = ''
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = 'select version from db_patches order by id desc limit 1;'
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            dbver = cursor.fetchone()[0]
            self.query_done("fgapiserver DB schema version: '%s'" % dbver)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return dbver

    """
      is_srv_reg - Return true if the service is registered
    """

    def is_srv_reg(self, service_uuid):
        db = None
        cursor = None
        safe_transaction = False
        is_reg = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = 'select count(*)>0 from srv_registry where uuid = %s;'
            sql_data = (service_uuid,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            is_reg = cursor.fetchone()[0]
            self.query_done("Service registration '%s' is '%s'"
                            % (service_uuid, is_reg))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return is_reg

    """
      srv_register - Register the given server and stores its current
                     configuration
    """

    def srv_register(self, fgapisrv_uuid, config):
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'insert into srv_registry (uuid,\n'
                '                          creation,\n'
                '                          last_access,\n'
                '                          enabled)\n'
                'values (%s,now(),now(),%s);'
            )
            sql_data = (fgapisrv_uuid, True)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Now save configuration settings
            for key in config.keys():
                key_value = "%s" % config[key]
                sql = (
                    'insert into srv_config (uuid,\n'
                    '                        name,\n'
                    '                        value,\n'
                    '                        enabled,\n'
                    '                        created,\n'
                    '                        modified)\n'
                    'values (%s, %s, %s, %s, now(), now());'
                )
                sql_data = (fgapisrv_uuid, key, key_value, True)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            # Calculate configuration hash
            sql = (
                'select md5(group_concat(value)) cfg_hash\n'
                'from srv_config\n'
                'where uuid = %s\n'
                'group by uuid;'
            )
            sql_data = (fgapisrv_uuid,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            cfg_hash = cursor.fetchone()[0]
            # Register calculated hash
            sql = 'update srv_registry set cfg_hash = %s where uuid = %s;'
            sql_data = (cfg_hash, fgapisrv_uuid)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Service registration queries executed
            self.query_done("Service with uuid: '%s' has been registered"
                            "and configuration parameters saved."
                            % fgapisrv_uuid)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)

    """
      srv_config - returns a dictionary containing configuration settings
                   of the service using its uuid value
    """

    def srv_config(self, fgapisrv_uuid):
        global fg_config
        db = None
        cursor = None
        safe_transaction = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select name,\n'
                '       value\n'
                'from srv_config\n'
                'where uuid=%s and enabled=%s;'
            )
            sql_data = (fgapisrv_uuid, True)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for config in cursor:
                kname = config[0]
                kvalue = config[1]
                fg_config[kname] = kvalue
            self.query_done("Configuration settings for service having "
                            "uuid: '%s' have been retrieved." % fgapisrv_uuid)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return fg_config

    """
      get_state returns the status and message of the last action on the DB
    """

    def get_state(self):
        """

        :rtype:
        """
        return self.err_flag, self.err_msg

    """
      create_session_token - Starting from the given triple
                            (username,password,timestamp) produce a
                            valid access token
    """

    def create_session_token(self, username, password, logts):
        # logtimestamp is currently ignored; old timestamps should not be
        # considered
        db = None
        cursor = None
        safe_transaction = True
        sestoken = ''
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select if(count(*)>0,\n'
                   '          if((select count(token)\n'
                   '              from fg_token t\n'
                   '              where t.subject = %s\n'
                   '                and t.creation+t.expiry>now()\n'
                   '              order by t.creation desc\n'
                   '              limit 1) > 0,\n'
                   '             concat(\'recycled\',\':\',\n'
                   '                    (select token\n'
                   '                     from fg_token t\n'
                   '                     where t.subject = %s\n'
                   '                     and t.creation+t.expiry>now()\n'
                   '                     order by t.creation desc\n'
                   '                     limit 1)),\n'
                   '             concat(\'new\',\':\',uuid())),\n'
                   '          NULL) acctoken\n'
                   'from fg_user u\n'
                   'where u.name=%s\n'
                   '  and u.password=sha(%s);')
            sql_data = (username, username, username, password)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            token_record = cursor.fetchone()[0]
            # Recycled token do not require the insertion
            if token_record is not None:
                token_fields = token_record.split(':')
                token_type = token_fields[0]
                sestoken = token_fields[1]
                # New token will be inserted
                if token_type == 'new':
                    sql = ('insert into fg_token (token,\n'
                           '                      subject,\n'
                           '                      user_id,\n'
                           '                      creation,\n'
                           '                      expiry)\n'
                           '  select %s, %s, id, now() creation, 24*60*60\n'
                           '  from  fg_user u\n'
                           '  where u.name=%s\n'
                           '    and u.password=sha(%s);')
                    sql_data = (sestoken, username, username, password)
                elif token_type == 'recycled':
                    sql = (
                        'update fg_token set creation = now()'
                        ' where token = %s')
                    sql_data = (sestoken,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            else:
                sestoken = ''
            self.query_done("session token is '%s'" % sestoken)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return sestoken

    """
      verify_session_token - Check if the passed token is valid and return
                             the user id and its name
    """

    def verify_session_token(self, sestoken):
        db = None
        cursor = None
        safe_transaction = False
        user_id = ''
        user_name = ''
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select if((creation+expiry)-now()>0,user_id,NULL) user_id\n'
                '      ,(select name from fg_user where id=user_id) name\n'
                'from fg_token\n'
                'where token=%s;')
            sql_data = (sestoken,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            user_rec = cursor.fetchone()
            if user_rec is not None:
                user_id = user_rec[0]
                user_name = user_rec[1]
            self.query_done(
                ("session token: '%s' -> "
                 "user_id='%s', "
                 "user_name='%s'" % (sestoken,
                                     user_id,
                                     user_name)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return user_id, user_name

    """
      get_token_info - Retrieve information about a given session token
    """

    def get_token_info(self, sestoken):
        db = None
        cursor = None
        safe_transaction = False
        token_info = {'token': sestoken, }
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select user_id\n'
                '      ,(select name from fg_user where id=user_id) name\n'
                '      ,creation,\n'
                '      ,expiry\n'
                '      ,(creation+expiry)-now()>0\n'
                '      ,if((creation+expiry)-now()>0,\n'
                '          (creation+expiry)-now(),\n'
                '          0) lasting\n'
                'from fg_token\n'
                'where token=%s;')
            sql_data = (sestoken,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            user_rec = cursor.fetchone()
            if user_rec is not None:
                token_info['user_id'] = user_rec[0]
                token_info['user_name'] = user_rec[1]
                token_info['creation'] = self.date_format(user_rec[2])
                token_info['expiry'] = user_rec[3]
                token_info['valid'] = user_rec[4] == 1
                token_info['lasting'] = user_rec[5]
            self.query_done(
                ("session token: '%s' -> "
                 "user_id='%s', "
                 "user_name='%s', "
                 "creation='%s', "
                 "expiry='%s', "
                 "valid='%s', "
                 "lasting='%s'"
                 % (sestoken,
                    token_info['user_id'],
                    token_info['user_name'],
                    token_info['creation'],
                    token_info['expiry'],
                    token_info['valid'],
                    token_info['lasting'])))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return token_info

    """
      register_token - Register the incoming and valid token into the token
                       table. This is used by PTV which bypass APIServer
                       session tokens. The record will be written only once
    """

    def register_token(self, userid, token, subject):
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            if token is not None:
                sql = ('insert into \n'
                       'fg_token (token, subject, user_id, creation, expiry)\n'
                       'select %s, %s, %s, now(), NULL\n'
                       'from dual\n'
                       'where (select count(*)\n'
                       '       from fg_token\n'
                       '       where token=%s) = 0;')
                sql_data = (token, subject, userid, token)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                self.query_done("token: '%s' successfully registered" % token)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return

    """
      user_token - Retrieve user info from given token
    """

    def user_token(self, token):
        db = None
        cursor = None
        safe_transaction = False
        user = {}
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            if token is not None:
                sql = ('select user_id, subject\n'
                       'from fg_token\n'
                       'where token = %s\n'
                       '  and creation+expiry > now();')
                sql_data = (token,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                user_rec = cursor.fetchone()
                if user_rec is not None:
                    user['id'] = user_rec[0]
                    user['name'] = user_rec[1]
                    self.query_done(
                        ("User id: '%s' "
                         "user name: '%s'" %
                         (user['id'],
                          user['name'])))
            else:
                self.query_done(
                    "No user record for token: %s" % token)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return user

    """
      create_delegated_token - Create a new delegated token for a given user
                               using the given token as reference
    """

    def create_delegated_token(self, token, username):
        db = None
        cursor = None
        safe_transaction = True
        sestoken = ''
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select if(count(*)>0,\n'
                   '          if((select count(token)\n'
                   '              from fg_token t\n'
                   '              where t.subject = %s\n'
                   '                and t.creation+t.expiry>now()\n'
                   '              order by t.creation desc\n'
                   '              limit 1) > 0,\n'
                   '             concat(\'recycled\',\':\',\n'
                   '                    (select token\n'
                   '                     from fg_token t\n'
                   '                     where t.subject = %s\n'
                   '                     and t.creation+t.expiry>now()\n'
                   '                     order by t.creation desc\n'
                   '                     limit 1)),\n'
                   '             concat(\'new\',\':\',uuid())),\n'
                   '          NULL) acctoken\n'
                   'from fg_user u\n'
                   'where u.name=%s\n'
                   '  and (select creation+expiry > now()\n'
                   '       from fg_token\n'
                   '       where token = %s);')
            sql_data = (username, username, username, token)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            token_record = cursor.fetchone()[0]
            # Recycled token do not require the insertion
            if token_record is not None:
                token_fields = token_record.split(':')
                token_type = token_fields[0]
                sestoken = token_fields[1]
                # New token will be inserted
                if token_type == 'new':
                    sql = ('insert into fg_token (token,\n'
                           '                      subject,\n'
                           '                      user_id,\n'
                           '                      creation,\n'
                           '                      expiry)\n'
                           '  select %s, %s, id, now() creation, 24*60*60\n'
                           '  from  fg_user u\n'
                           '  where u.name=%s;')
                    sql_data = (sestoken, username, username,)
                elif token_type == 'recycled':
                    sql = ('update fg_token set creation = now()'
                           ' where token = %s')
                    sql_data = (sestoken,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            else:
                sestoken = ''
            self.query_done("session token is '%s'" % sestoken)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return sestoken

    """
      verify_user_role - Verify if the given user has the given roles
                         Role list is a comma separated list of names
                         The result is successful only if all roles  in
                         the list are satisfied
    """

    def verify_user_role(self, user, roles):
        db = None
        cursor = None
        safe_transaction = False
        result = 1
        user_id = self.user_param_to_user_id(user)
        for role_name in roles.split(','):
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                sql = ('select count(*)>0      \n'
                       'from fg_user        u  \n'
                       '    ,fg_group       g  \n'
                       '    ,fg_user_group ug  \n'
                       '    ,fg_group_role gr  \n'
                       '    ,fg_role        r  \n'
                       'where u.id=%s          \n'
                       '  and u.enabled = true \n'
                       '  and u.id=ug.user_id  \n'
                       '  and g.id=ug.group_id \n'
                       '  and g.id=gr.group_id \n'
                       '  and r.id=gr.role_id  \n'
                       '  and r.name = %s;')
                sql_data = (user_id, role_name)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                hasrole = cursor.fetchone()[0]
                result *= hasrole
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
                result = 0
                break
            finally:
                self.close_db(db, cursor, safe_transaction)
        self.query_done(
            ("role(s) '%s' for user_id '%s' is %s'" % (roles,
                                                       user_id,
                                                       result > 0)))
        return result != 0

    """
      user_param_to_user_id - Retrieve the user id from an user parameter
    """

    def user_param_to_user_id(self, user):
        user_id = None
        if user is not None:
            try:
                user_id = int(user)
            except ValueError:
                user_id = self.get_user_id_by_name(user)
        return user_id

    """
      get_user_id_by_name - Retrieve the id of a given user name
    """

    def get_user_id_by_name(self, user_name):
        db = None
        cursor = None
        safe_transaction = False
        user_id = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id\n'
                   'from fg_user\n'
                   'where name=%s;')
            sql_data = (user_name,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()
            if result is not None:
                user_id = result[0]
            self.query_done(
                "User with name: '%s' has id: %s " % (user_name, user_id))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return user_id

    """
      app_param_to_app_id - Retrieve the application id from an application
                            parameter
    """

    def app_param_to_app_id(self, application):
        app_id = None
        if application is not None:
            try:
                app_id = int(application)
            except ValueError:
                app_id = self.get_app_id_by_name(application)
        return app_id

    """
      get_app_id_by_name - Retrieve the id of a given user name
    """

    def get_app_id_by_name(self, app_name):
        db = None
        cursor = None
        safe_transaction = False
        app_id = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id\n'
                   'from application\n'
                   'where name=%s;')
            sql_data = (app_name,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()
            if result is not None:
                app_id = result[0]
            self.query_done(
                "Application with name: '%s' has id: %s "
                % (app_name, app_id))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_id

    """
      group_param_to_group_id - Retrieve the group id from a group parameter
    """

    def group_param_to_group_id(self, group):
        group_id = None
        if group is not None:
            try:
                group_id = int(group)
            except ValueError:
                group_id = self.get_group_id_by_name(group)
        return group_id

    """
      get_group_id_by_name - Retrieve the id of a given group name
    """

    def get_group_id_by_name(self, group_name):
        db = None
        cursor = None
        safe_transaction = False
        group_id = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id\n'
                   'from fg_group\n'
                   'where name=%s;')
            sql_data = (group_name,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()
            if result is not None:
                group_id = result[0]
            self.query_done(
                "Group with name: '%s' has id: %s "
                % (group_name, group_id))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return group_id

    """
      verify_user_app - Verify if the given user has the given app in its roles
    """

    def verify_user_app(self, user, application):
        db = None
        cursor = None
        safe_transaction = False
        user_id = self.user_param_to_user_id(user)
        app_id = self.app_param_to_app_id(application)
        result = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)>0      \n'
                   'from fg_user        u  \n'
                   '    ,fg_group       g  \n'
                   '    ,application    a  \n'
                   '    ,fg_user_group ug  \n'
                   '    ,fg_group_apps ga  \n'
                   'where u.id=%s          \n'
                   '  and u.id=ug.user_id  \n'
                   '  and a.id=%s          \n'
                   '  and a.id=ga.app_id   \n'
                   '  and g.id=ug.group_id \n'
                   '  and g.id=ga.group_id;')
            sql_data = (user_id, app_id)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()[0]
            self.query_done(
                "User id '%s' access to application "
                "id '%s' is %s'" % (user_id,
                                    app_id,
                                    result > 0))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      same_group - Return True if given users belong to the same group
    """

    def same_group(self, user_1, user_2):
        db = None
        cursor = None
        safe_transaction = False
        result = ''
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)>1               \n'
                   'from fg_user_group              \n'
                   'where user_id = (select id      \n'
                   '                 from fg_user   \n'
                   '                 where name=%s) \n'
                   '   or user_id = (select id      \n'
                   '                 from fg_user   \n'
                   '                 where name=%s) \n'
                   'group by group_id               \n'
                   'having count(*) > 1;')
            sql_data = (user_1, user_2)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            if record is not None:
                result = record[0]
            self.query_done(
                ("same group for user '%s' "
                 "and '%s' is %s" % (user_1,
                                     user_2,
                                     result > 0)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      get_user_info_by_name - Return full user info from the given username
    """

    def get_user_info_by_name(self, name):
        db = None
        cursor = None
        safe_transaction = False
        user_info = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id        \n'
                   '      ,name      \n'
                   '      ,password  \n'
                   '      ,first_name\n'
                   '      ,last_name \n'
                   '      ,institute \n'
                   '      ,mail      \n'
                   '      ,creation  \n'
                   '      ,modified  \n'
                   'from fg_user     \n'
                   'where name=%s;')
            sql_data = (name,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            if record is not None:
                user_info = {
                    "id": record[0],
                    "name": record[1],
                    "password": record[2],
                    "first_name": record[3],
                    "last_name": record[4],
                    "institute": record[5],
                    "mail": record[6],
                    "creation": self.date_format(record[7]),
                    "modified": self.date_format(record[8])}
            self.query_done(
                "User '%s' info: '%s'" % (name, user_info))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return user_info

    """
      get_ptv_groups - Scan the given array of groups to identify
                       valid FG groups returning only valid group names
    """

    def get_ptv_groups(self, portal_groups):
        db = None
        cursor = None
        safe_transaction = False
        fg_groups = []
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for group in portal_groups:
                sql = 'select count(*) from fg_group where lower(name)=%s;'
                sql_data = (group,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                record = cursor.fetchone()[0]
                if record > 0:
                    fg_groups.append(group)
                else:
                    logging.warn("Group '%s' does not exists" % group)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        self.query_done(
            "Passed groups: '%s' -> valid groups: '%s'" % (portal_groups,
                                                           fg_groups))
        return fg_groups

    """
      register_ptv_subject - Check and eventually register the given subject
                             as a fgAPIServer user. The portal_user field
                             contains the returned PTV subject value
                            the fg_groups contains a list of groups associated
                            to the user
    """

    def register_ptv_subject(self, portal_user, fg_groups):
        db = None
        cursor = None
        safe_transaction = True
        user_record = (None, None)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = 'select id, name from fg_user where name=%s;'
            sql_data = (portal_user,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            user_record = cursor.fetchone()
            if user_record is not None:
                self.query_done(
                    "PTV user '%s' record: '%s'" % (portal_user,
                                                    user_record))
                return user_record[0], user_record[1]
            # The ptv subject does not exists
            # register it as new user using groups
            # information to associate correct groups
            # Create the user
            sql = ('insert into fg_user (name, \n'
                   '                     password,\n'
                   '                     first_name,\n'
                   '                     last_name,\n'
                   '                     institute,\n'
                   '                     mail,\n'
                   '                     creation,\n'
                   '                     modified)\n'
                   'values (%s,\n'
                   '        sha(\'NOPASSWORD\'),\n'
                   '        \'PTV_TOKEN\',\n'
                   '        \'PTV_TOKEN\',\n'
                   '        \'PTV_TOKEN\',\n'
                   '        \'PTV@TOKEN\',\n'
                   '        now(),\n'
                   '        now());')
            sql_data = (portal_user,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Retrieve the inserted user_id
            sql = 'select max(id) from fg_user;'
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            user_id = cursor.fetchone()[0]
            # Associate groups
            for group_name in fg_groups:
                sql = 'select id from fg_group where name=%s;'
                sql_data = (group_name,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                group_id = cursor.fetchone()[0]
                sql = ('insert into fg_user_group (user_id,\n'
                       '                           group_id,\n'
                       '                           creation)\n'
                       'values (%s,%s,now());')
                sql_data = (user_id, group_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            user_record = (user_id, portal_user)
            self.query_done(
                "Portal user '%s' successfully inserted" % portal_user)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return user_record

    """
      task_exists - Return True if the given task_id exists False otherwise
    """

    def task_exists(self, task_id, user, user_name):
        db = None
        cursor = None
        safe_transaction = False
        v_user = []
        v_task = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = 'select name from fg_user where id = %s;'
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            v_user.append(cursor.fetchone()[0])
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        if v_user[0] != user_name:
            v_user.append(user_name)
        for user_name in v_user:
            v_task += self.get_task_list(user_name, None)
        self.query_done("Task '%s' exists is %s" %
                        (task_id, int(task_id) in v_task))
        return int(task_id) in v_task

    """
       get_task_record - Retrieve the whole task information
    """

    def get_task_record(self, task_id):
        db = None
        cursor = None
        safe_transaction = False
        task_record = {}
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # Task record
            sql = (
                'select '
                ' id\n'
                ',status\n'
                ',creation\n'
                ',last_change\n'
                ',app_id\n'
                ',description\n'
                ',user\n'
                ',iosandbox\n'
                'from task\n'
                'where id=%s\n'
                '  and status != \'PURGED\';')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            task_dbrec = cursor.fetchone()
            if task_dbrec is not None:
                task_dicrec = {
                    "id": str(
                        task_dbrec[0]),
                    "status": task_dbrec[1],
                    "creation": self.date_format(task_dbrec[2]),
                    "last_change": self.date_format(task_dbrec[3]),
                    "application": task_dbrec[4],
                    "description": task_dbrec[5],
                    "user": task_dbrec[6],
                    "iosandbox": task_dbrec[7]}
            else:
                self.query_done("Task '%s' not found" % task_id)
                return {}
            # Task arguments
            sql = ('select argument\n'
                   'from task_arguments\n'
                   'where task_id=%s\n'
                   'order by arg_id asc;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            task_args = []
            for arg in cursor:
                task_args += [arg[0], ]
            # Task input files
            sql = (
                'select file\n'
                '      ,if(path is null or length(path)=0,'
                '          \'NEEDED\','
                '          \'READY\') status\n'
                '      ,if(path is NULL,\'\',path)\n'
                'from task_input_file\n'
                'where task_id=%s\n'
                'order by file_id asc;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            task_ifiles = []
            for ifile in cursor:
                if ifile[1] == 'NEEDED':
                    ifile_entry = {
                        "name": ifile[0],
                        "status": ifile[1],
                    }
                else:
                    ifile_entry = {
                        "name": ifile[0],
                        "status": ifile[1],
                        "url": 'file?%s'
                               % urllib.urlencode({"path": ifile[2],
                                                   "name": ifile[0]}),
                    }
                task_ifiles += [ifile_entry, ]
            # Task output files
            sql = ('select file\n'
                   '      ,if(path is NULL,\'\',path)\n'
                   'from task_output_file\n'
                   'where task_id=%s\n'
                   'order by file_id asc;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            task_ofiles = []
            for ofile in cursor:
                file_url = ''
                if ofile[1] != '':
                    file_url = 'file?%s' % urllib.urlencode({"path": ofile[1],
                                                             "name": ofile[0]})
                ofile_entry = {"name": ofile[0],
                               "url": file_url}
                task_ofiles += [ofile_entry, ]
            # runtime_data
            sql = (
                'select '
                '  data_name\n'
                ' ,data_value\n'
                ' ,data_desc\n'
                ' ,data_type\n'
                ' ,data_proto\n'
                ' ,creation\n'
                ' ,last_change\n'
                'from runtime_data\n'
                'where task_id=%s\n'
                'order by data_id asc;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            runtime_data = []
            for rtdata in cursor:
                rtdata_entry = {
                    "name": rtdata[0],
                    "value": rtdata[1],
                    "description": rtdata[2],
                    "type": rtdata[3],
                    "proto": rtdata[4],
                    "creation": self.date_format(rtdata[5]),
                    "last_change": self.date_format(rtdata[6])}
                runtime_data += [rtdata_entry, ]
            # Prepare output
            task_record = {
                "id": str(
                    task_dicrec['id']),
                "status": task_dicrec['status'],
                "creation": task_dicrec['creation'],
                "last_change": task_dicrec['last_change'],
                "application": str(
                    task_dicrec['application']),
                "description": task_dicrec['description'],
                "user": task_dicrec['user'],
                "arguments": task_args,
                "input_files": task_ifiles,
                "output_files": task_ofiles,
                "runtime_data": runtime_data,
                "iosandbox": task_dicrec['iosandbox']}
            self.query_done(
                "Task '%s' record: '%s'" % (task_id,
                                            task_record))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return task_record

    """
      get_task_status - Return the status of a given Task
    """

    def get_task_status(self, task_id):
        return self.get_task_record(task_id).get('status', None)

    """
      get_task_input_files - Return info about input files of a given Task
    """

    def get_task_input_files(self, task_id):
        db = None
        cursor = None
        safe_transaction = False
        task_ifiles = ()
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,if(path is null,\'NEEDED\',\'READY\') status\n'
                   'from task_input_file\n'
                   'where task_id = %s;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for ifile in cursor:
                file_info = {
                    "name": ifile[0], "status": ifile[1]
                }
                task_ifiles += (file_info,)
            self.query_done(
                "Input files for task '%s': '%s'" % (task_id,
                                                     task_ifiles))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return task_ifiles

    """
      get_task_output_files - Return info about output files of a given Task
    """

    def get_task_output_files(self, task_id):
        db = None
        cursor = None
        safe_transaction = False
        task_ofiles = ()
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,if(path is null,\'waiting\',\'ready\')\n'
                   'from task_output_file\n'
                   'where task_id = %s;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for ofile in cursor:
                file_info = {
                    "name": ofile[0], "status": ofile[1]
                }
                task_ofiles += (file_info,)
            self.query_done(
                "Output files for task '%s': '%s'" % (task_id,
                                                      task_ofiles))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return task_ofiles

    """
      get_app_detail - Return details about a given app_id
    """

    def get_app_detail(self, application):
        db = None
        cursor = None
        safe_transaction = False
        app_detail = {}
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,outcome\n'
                '      ,creation\n'
                '      ,enabled\n'
                'from application\n'
                'where id=%s;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_record = cursor.fetchone()
            app_detail = {
                "id": str(
                    app_record[0]),
                "name": app_record[1],
                "description": app_record[2],
                "outcome": app_record[3],
                "creation": self.date_format(app_record[4]),
                "enabled": bool(app_record[5])}
            # Add now app parameters
            sql = ('select pname\n'
                   '      ,pvalue\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   'order by param_id asc;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_parameters = []
            for param in cursor:
                parameter = {
                    "param_name": param[0], "param_value": param[1]
                }
                app_parameters += [parameter, ]
            app_detail['parameters'] = app_parameters
            # Get now application ifnrastructures with their params
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,creation\n'
                '      ,if(enabled,\'enabled\',\'disabled\') status\n'
                '      ,if(vinfra,\'virtual\',\'real\') status\n'
                'from infrastructure\n'
                'where app_id=%s;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            infrastructures = []
            for infra in cursor:
                infra_details = {
                    "id": str(
                        infra[0]),
                    "name": infra[1],
                    "description": infra[2],
                    "creation": self.date_format(infra[3]),
                    "status": infra[4],
                    "virtual": infra[5]}
                infrastructures += [infra_details, ]
            # Now loop over infrastructures to get their parameters
            for infra in infrastructures:
                sql = ('select pname, pvalue\n'
                       'from infrastructure_parameter\n'
                       'where infra_id=%s\n'
                       'order by param_id asc;')
                sql_data = (str(infra['id']),)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                infra_parameters = []
                for param in cursor:
                    param_details = {
                        "name": param[0], "value": param[1]
                    }
                    infra_parameters += [param_details, ]
                infra['parameters'] = infra_parameters
            app_detail['infrastructures'] = infrastructures
            self.query_done(
                "Details for app '%s': '%s'" % (app_id, app_detail))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_detail

    """
      get_task_app_detail - Return application details of a given Task
    """

    def get_task_app_detail(self, task_id):
        task_record = self.get_task_record(task_id)
        return self.get_app_detail(str(task_record['application']))

    """
      get_task_info - Retrieve full information about given task_id
    """

    def get_task_info(self, task_id):
        task_record = self.get_task_record(task_id)
        task_record.get('id', None)
        if task_record.get('id', None) is None:
            self.err_flag = True
            self.err_msg = "[ERROR] Did not find task id: %s" % task_id
            return {}
        task_app_details = self.get_task_app_detail(task_id)
        task_info = task_record
        del task_info['application']
        task_info['application'] = task_app_details
        self.query_done(
            "Task '%s' info: '%s'" % (task_id, task_info))
        return task_info

    """
        get_app_files - Retrieve from application_files table the application
                        specific files associated to the given application
    """

    def get_app_files(self, application):
        db = None
        cursor = None
        safe_transaction = False
        app_files = []
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,path\n'
                   '      ,override\n'
                   'from application_file\n'
                   'where app_id=%s\n'
                   'order by file_id asc;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for app_file in cursor:
                app_files += [{"file": app_file[0],
                               "path": app_file[1],
                               "override": bool(app_file[2])}, ]
            self.query_done(
                "Files for application '%s': '%s'" % (app_id, app_files))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_files

    """
      init_task - initialize a task from a given application id
    """

    def init_task(
            self,
            application,
            description,
            user,
            arguments,
            input_files,
            output_files):
        app_id = self.app_param_to_app_id(application)
        # Get app defined files
        app_files = self.get_app_files(app_id)
        logging.debug("Application files for app_id %s are: %s"
                      % (app_id, app_files))
        # Start creating task
        db = None
        cursor = None
        safe_transaction = True
        task_id = -1
        try:
            # Create the Task IO Sandbox
            iosandbox = '%s/%s' % (self.iosandbbox_dir, str(uuid.uuid1()))
            os.makedirs(iosandbox)
            os.chmod(iosandbox, 0770)
            # Insert new Task record
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('insert into task (id\n'
                   '                 ,creation\n'
                   '                 ,last_change\n'
                   '                 ,app_id\n'
                   '                 ,description\n'
                   '                 ,status\n'
                   '                 ,user\n'
                   '                 ,iosandbox)\n'
                   'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
                   '      ,now()                           -- creation date\n'
                   '      ,now()                           -- last change\n'
                   '      ,%s                              -- app_id\n'
                   '      ,%s                              -- description\n'
                   '      ,\'WAITING\'                     -- status WAITING\n'
                   '      ,%s                              -- user\n'
                   '      ,%s                              -- iosandbox\n'
                   'from task;\n')
            sql_data = (app_id, description, user, iosandbox)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = 'select max(id) from task;'
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql)
            task_id = cursor.fetchone()[0]
            # Insert Task arguments
            if arguments is not []:
                for arg in arguments:
                    sql = (
                        'insert into task_arguments (task_id\n'
                        '                           ,arg_id\n'
                        '                           ,argument)\n'
                        'select %s\n'
                        '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)\n'
                        '      ,%s\n'
                        'from task_arguments\n'
                        'where task_id=%s')
                    sql_data = (task_id, arg, task_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)

            # Process input files specified in the REST URL (input_files)
            # producing a new vector called task_input_file having the same
            # structure of app_files: [ { "name": <filname>
            #                             ,"path": <path to file> },...]
            # except for the 'override' key not necessary in this second array.
            # For each file specified inside input_file, verify if it exists
            # alredy in the app_file vector. If the file exists there are two
            # possibilities:
            # * app_file['override'] flag is true; then user inputs are
            #   ignored, thus the file will be skipped
            # * app_file['override'] flag is false; user input couldn't be
            #   ignored, thus the path to the file will be set to NULL waiting
            #   for user input
            logging.debug("Input files processing")
            task_input_files = []
            for input_file in input_files:
                logging.debug("file: %s" % input_file)
                skip_file = False
                for app_file in app_files:
                    if input_file['name'] == app_file['file']:
                        skip_file = True
                        if app_file['override'] is True:
                            break
                        else:
                            app_file['path'] = None
                            break
                if not skip_file:
                    # The file is not in app_file
                    task_input_files += [{"path": None,
                                          "file": input_file['name']}, ]

            # Files can be registered in task_input_files
            for inpfile in app_files + task_input_files:
                # Not None paths having not empty content refers to an
                # existing app_file that could be copied into the iosandbox
                # task directory and path can be modifies with the iosandbox
                # path
                if inpfile['path'] is not None and len(inpfile['path']) > 0:
                    shutil.copy(
                        '%s/%s' %
                        (inpfile['path'], inpfile['file']), '%s/%s' %
                        (iosandbox, inpfile['file']))
                    inpfile['path'] = iosandbox
                sql = (
                    'insert into task_input_file (task_id\n'
                    '                            ,file_id\n'
                    '                            ,path\n'
                    '                            ,file)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    '      ,%s\n'
                    'from task_input_file\n'
                    'where task_id=%s')
                sql_data = (task_id, inpfile['path'], inpfile['file'], task_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            # Insert Task output_files specified by application settings
            # (default)
            sql = ('select pvalue\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   ' and (   pname=\'jobdesc_output\'\n'
                   '      or pname=\'jobdesc_error\');')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for out_file in cursor:
                output_files += [{"name": out_file[0]}, ]
            # Insert Task output_files specified by user
            for outfile in output_files:
                sql = (
                    'insert into task_output_file (task_id\n'
                    '                             ,file_id\n'
                    '                             ,file)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    'from task_output_file\n'
                    'where task_id=%s')
                sql_data = (task_id, outfile['name'], task_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            self.query_done(
                "Task successfully inserted with id: '%s'" % task_id)
        except IOError as xxx_todo_changeme:
            (errno, strerror) = xxx_todo_changeme.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)

        # Accordingly to specs: input_files -
        # If omitted the task is immediately ready to start
        # If the inputsandbox is ready the job will be triggered for execution
        if self.is_input_sandbox_ready(task_id):
            # The input_sandbox is completed; trigger the Executor for this
            # task only if the completed sandbox consists of overridden files
            # or no files are specified in the application_file table for this
            # app_id
            if self.is_overridden_sandbox(app_id):
                if not self.submit_task(task_id):
                    logging.debug("Unable to submit taks: '%s'"
                                  % self.err_msg)
            else:
                logging.debug("Task %s needs to finalize its input sandbox")

        return task_id

    """
      setup_default_inputs - process the application_file table and update the
                             task_input_file having null paths; thus inserting
                             default application files in to the task inputs
                             (see POST action in /tasks/<id>/input endpoint)
    """

    def setup_default_inputs(self, task_id, task_sandbox):
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,path\n'
                   'from application_file\n'
                   'where app_id = (select app_id\n'
                   '                from task\n'
                   '                where id=%s)'
                   '  and path is not NULL;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            def_app_files = []
            for app_file_rec in cursor:
                def_app_files += [{"file": app_file_rec[0],
                                   "path": app_file_rec[1]}, ]
            for app_file in def_app_files:
                shutil.copy('%s/%s' % (app_file['path'], app_file['file']),
                            '%s/%s' % (task_sandbox, app_file['file']))
                sql = ('update task_input_file\n'
                       'set path=%s\n'
                       'where file=%s\n'
                       '  and task_id=%s\n'
                       '  and path is null;')
                sql_data = (app_file['path'], app_file['file'], task_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            self.query_done(
                "Default input files for task '%s' successfully processed"
                % task_id)
        except IOError as xxx_todo_changeme:
            (errno, strerror) = xxx_todo_changeme.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)

    """
      get_task_io_sandbox - Get the assigned IO Sandbox folder of the
                            given task_id
    """

    def get_task_io_sandbox(self, task_id):
        db = None
        cursor = None
        safe_transaction = False
        iosandbox = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = 'select iosandbox from task where id=%s;'
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()
            if result is None:
                self.err_flag = True
                self.err_msg = "[ERROR] Unable to find task id: %s" % task_id
            else:
                iosandbox = result[0]
                self.query_done(
                    "IO sandbox for task '%s': '%s'" % (task_id, iosandbox))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return iosandbox

    """
      update_input_sandbox_file - Update input_sandbox_table with the fullpath
      of a given (task_id, filename, filepat filepath)
    """

    def update_input_sandbox_file(self, task_id, filename, filepath):
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('update task_input_file\n'
                   'set path=%s\n'
                   'where task_id=%s\n'
                   '  and file=%s;')
            sql_data = (filepath, task_id, filename)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            self.query_done(
                "input sandbox for task '%s' successfully updated" % task_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return

    """
      is_input_sandbox_ready - Return true if all input_sandbox files have been
                               uploaded for a given (task_id)
                               True if all files have a file path registered
                               or the task does not contain any input file
    """

    def is_input_sandbox_ready(self, task_id):
        db = None
        cursor = None
        safe_transaction = False
        sandbox_ready = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select '
                '  sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
                'from task_input_file\n'
                'where task_id=%s;')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sandbox_ready = cursor.fetchone()[0]
            self.query_done(
                "sandbox ready for task '%s' is %s"
                % (task_id, 1 == int(sandbox_ready)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return 1 == int(sandbox_ready)

    """
      submit_task - Trigger the GridEngine to submit the given task
                    This function takes care of all APIServerDaemon needs to
                    properly submit the applciation
    """

    def submit_task(self, task_id):
        # Get task information
        task_info = self.get_task_info(task_id)
        app_info = task_info['application']
        app_params = app_info['parameters']
        # Retrieve only enabled infrastructures
        app_infras = ()
        for infra in app_info['infrastructures']:
            if bool(infra['status']):
                app_infras += (infra,)
        if app_infras is None or len(app_infras) == 0:
            self.err_flag = True
            self.err_msg = ('No suitable infrastructure found for task_id: %s'
                            % task_id)
            return False
        # Proceed only if task comes form a WAITING state
        task_status = task_info.get('status', '')
        if task_status != 'WAITING':
            self.err_flag = True
            self.err_msg = ('Wrong status (\'%s\') '
                            'to ask submission for task_id: %s') % (
                               task_status, task_id)
            return False
        # Application must be also enabled
        if not bool(app_info['enabled']):
            self.err_flag = True
            self.err_msg = ('Unable submit task_id: %s,'
                            ' because application is disabled') % task_id
            return False
        # Infrastructures must exist for this application
        enabled_infras = []
        for infra in app_infras:
            if infra['status'] == 'enabled':
                enabled_infras += [infra, ]
        if len(enabled_infras) == 0:
            self.err_flag = True
            self.err_msg = ('No suitable infrastructures found for task_id: %s'
                            % task_id)
            return False
        # All checks have been done, it is possible to enqueue the Task request
        return self.enqueue_task_request(task_info)

    """
      enqueue_task_request - Place a request into the queue
    """

    def enqueue_task_request(self, task_info):
        db = None
        cursor = None
        safe_transaction = True
        self.err_flag = False
        as_file = None
        try:
            # Save native APIServer JSON file, having the format:
            # <task_iosandbox_dir>/<task_id>.json
            as_file = open('%s/%s.json' %
                           (task_info['iosandbox'], task_info['id']), "w")
            as_file.write(json.dumps(task_info))
            # Determine the application target executor (default GridEngine)
            target_executor = 'GridEngine'
            for app_param in task_info['application']['parameters']:
                if app_param['param_name'] == 'target_executor':
                    target_executor = app_param['param_value']
                    break
            try:
                # Insert task record in the APIServerDaemon' queue
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                sql = (
                    'insert into as_queue (\n'
                    '   task_id       \n'
                    '  ,target_id     \n'
                    '  ,target        \n'
                    '  ,action        \n'
                    '  ,status        \n'
                    '  ,target_status \n'
                    '  ,creation      \n'
                    '  ,last_change   \n'
                    '  ,check_ts      \n'
                    '  ,action_info   \n'
                    ') values (%s,\n'
                    '          NULL,\n'
                    '          %s,\n'
                    '          \'SUBMIT\',\n'
                    '          \'QUEUED\',\n'
                    '          NULL,\n'
                    '          now(),\n'
                    '          now(),\n'
                    '          now(),\n'
                    '          %s);')
                sql_data = (task_info['id'],
                            target_executor, task_info['iosandbox'])
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                sql = (
                    'update task set status=\'SUBMIT\', \n'
                    'last_change=now() where id=%s;')
                sql_data = (str(task_info['id']),)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                self.query_done(
                    "Task '%s' enqueued successfully" % task_info)
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
                if as_file is not None:
                    as_file.close()
        except IOError as e:
            (errno, strerror) = e.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        finally:
            if as_file is not None:
                as_file.close()
        return not self.err_flag

    """
      get_task_list - Get the list of tasks associated to a user and/or app_id
    """

    def get_task_list(self, user, application):
        db = None
        cursor = None
        safe_transaction = False
        task_ids = []
        app_id = self.app_param_to_app_id(application)
        try:
            # Get Task ids preparing the right query (user/*,@
            # wildcards/app_id)
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            app_clause = ''
            sql_data = ()
            user_filter = user[0]
            if user_filter == '*':
                user_clause = ''
            elif user_filter == '@':
                user_name = user[1:]
                user_clause = (
                    '  and user in (select distinct(u.name)      \n'
                    '               from fg_user        u        \n'
                    '                  , fg_group       g        \n'
                    '                  , fg_user_group ug        \n'
                    '               where u.id=ug.user_id        \n'
                    '                 and g.id=ug.group_id       \n'
                    '                 and g.id in                \n'
                    '                   (select g.id             \n'
                    '                    from fg_user_group ug   \n'
                    '                        ,fg_user        u   \n'
                    '                        ,fg_group       g   \n'
                    '                     where ug.user_id=u.id  \n'
                    '                       and ug.group_id=g.id \n'
                    '                       and u.name=%s))')
                sql_data += (user_name,)
            else:
                user_name = user
                user_clause = '  and user = %s\n'
                sql_data += (user_name,)
            if app_id is not None:
                app_clause = '  and app_id = %s\n'
                sql_data += (app_id,)
            sql = ('select id\n'
                   'from task\n'
                   'where status != \'PURGED\'\n'
                   '%s%s'
                   'order by id desc;'
                   ) % (user_clause, app_clause)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for task_id in cursor:
                task_ids.append(task_id[0])
            self.query_done(
                "Task list for user '%s', app '%s': '%s'" % (user,
                                                             app_id,
                                                             task_ids))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return task_ids

    """
      delete - Delete a given task
    """

    def delete(self, task_id):
        db = None
        cursor = None
        safe_transaction = True
        status = False
        # Get task information
        task_info = self.get_task_info(task_id)
        try:
            # Insert task record in the GridEngine' queue
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'insert into as_queue (\n'
                '   task_id\n'
                '  ,target_id\n'
                '  ,target\n'
                '  ,action\n'
                '  ,status\n'
                '  ,target_status\n'
                '  ,creation\n'
                '  ,last_change\n'
                '  ,check_ts\n'
                '  ,action_info\n'
                ') select %s,\n'
                '         NULL,\n'
                '         (select target\n'
                '          from as_queue\n'
                '          where task_id=%s\n'
                '          order by task_id asc\n'
                '          limit 1),\n'
                '         \'CLEAN\',\n'
                '         \'QUEUED\',\n'
                '         (select status\n'
                '          from as_queue\n'
                '          where task_id=%s\n'
                '          order by task_id asc\n'
                '          limit 1),\n'
                '         now(),\n'
                '         now(),\n'
                '         now(),\n'
                '         %s;')
            sql_data = (task_info['id'],
                        task_info['id'],
                        task_info['id'],
                        task_info['iosandbox'])
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = (
                'update task set status=\'CANCELLED\', '
                'last_change=now() where id=%s;')
            sql_data = (str(task_info['id']),)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            self.query_done("Task '%s' successfully deleted" % task_id)
            status = True
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return status

    """
      patch_task - Patches a given task with provided runtime_data values
    """

    def patch_task(self, task_id, runtime_data):
        db = None
        cursor = None
        safe_transaction = True
        status = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for rtdata in runtime_data:
                data_name = rtdata['data_name']
                data_value = rtdata['data_value']
                data_desc = rtdata.get('data_desc', '')
                data_type = rtdata.get('data_type', '')
                data_proto = rtdata.get('data_proto', '')
                # Determine if dataname exists for this task
                sql = ('select count(*)\n'
                       'from runtime_data\n'
                       'where data_name=%s\n'
                       '  and task_id=%s;')
                sql_data = (data_name, task_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result = cursor.fetchone()
                if result is None:
                    self.err_flag = True
                    self.err_msg = ("[ERROR] Unable to patch task id: %s"
                                    % task_id)
                else:
                    data_count = result[0]
                    if data_count == 0:
                        # First data insertion
                        sql = (
                            'insert into runtime_data (task_id\n'
                            '                         ,data_id\n'
                            '                         ,data_name\n'
                            '                         ,data_value\n'
                            '                         ,data_desc\n'
                            '                         ,data_type\n'
                            '                         ,data_proto\n'
                            '                         ,creation\n'
                            '                         ,last_change)\n'
                            'select %s\n'
                            '      ,(select '
                            '          if(max(data_id) is NULL,\n'
                            '             1,\n'
                            '             max(data_id)+1)\n'
                            '        from runtime_data\n'
                            '        where task_id=%s)\n'
                            '      ,%s\n'
                            '      ,%s\n'
                            '      ,%s\n'
                            '      ,%s\n'
                            '      ,%s\n'
                            '      ,now()\n'
                            '      ,now();\n')
                        sql_data = (task_id, task_id,
                                    data_name,
                                    data_value,
                                    data_desc,
                                    data_type,
                                    data_proto)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                        status = True
                    else:
                        sql = ('update runtime_data\n'
                               'set data_value = %s\n'
                               '   ,last_change = now()\n'
                               'where data_name=%s\n'
                               '  and task_id=%s;')
                        sql_data = (data_value, data_name, task_id)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                        status = True
            self.query_done(
                ("Runtime data '%s' successfully updated"
                 " on task '%s'" % (runtime_data, task_id)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return status

    """
    is_overridden_sandbox - True if all files of the specified application
                            have the override flag True
                            If no files are specified in application_file the
                            function returns True
    """

    def is_overridden_sandbox(self, application):
        db = None
        cursor = None
        safe_transaction = False
        no_override = False
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = (
                'select '
                '  if(sum(override) is NULL,'
                '     TRUE,'
                '     count(*)=sum(override)) override\n'
                'from application_file\n'
                'where app_id=%s;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            no_override = cursor.fetchone()[0]
            self.query_done(
                ("overridden sandbox "
                 "for app '%s' is %s" % (app_id,
                                         1 == int(no_override))))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return 1 == int(no_override)

    """
      get_file_task_id - Get the task id related to the given file and path
                         or null if no task is found with the given input
    """

    def get_file_task_id(self, file_name, file_path):
        db = None
        cursor = None
        safe_transaction = False
        task_id = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor(buffered=True)
            sql = ('select task_id from task_output_file\n'
                   'where file=%s and path=%s\n'
                   'union all\n'
                   'select task_id from task_input_file\n'
                   'where file=%s and path=%s\n'
                   'union all\n'
                   'select null;')
            sql_data = (file_name, file_path, file_name, file_path)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            task_id = cursor.fetchone()[0]
            self.query_done(
                ("task_id for file name '%s' "
                 "having path '%s' is: '%s'" % (file_name,
                                                file_path,
                                                task_id)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return task_id

    """
      get_file_app_id - Starting from path and filename get the corresponding
                        application id
    """

    def get_file_app_id(self, file_path, file_name):
        db = None
        cursor = None
        safe_transaction = False
        app_id = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select app_id from application_file\n'
                   'where file=%s and path=%s\n'
                   'union all\n'
                   'select null;')
            sql_data = (file_name, file_path)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_id = cursor.fetchone()[0]
            self.query_done(
                ("app_id for file name '%s' "
                 "having path '%s' is: '%s'" % (file_name,
                                                file_path,
                                                app_id)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_id

    """
      status_change - Add a task status change command in as_queue
                      this causes the EIs to handle the change properly
    """

    def status_change(self, task_id, new_status):
        db = None
        cursor = None
        safe_transaction = True
        result = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('insert into as_queue (task_id,\n'
                   '                      action,\n'
                   '                      status,\n'
                   '                      target,\n'
                   '                      target_status,\n'
                   '                      creation,\n'
                   '                      last_change,\n'
                   '                      check_ts,\n'
                   '                      action_info\n)'
                   'select %s,\n'
                   '       \'STATUSCH\',\n'
                   '       \'QUEUED\',\n'
                   '       (select target\n'
                   '        from as_queue\n'
                   '        where task_id=%s\n'
                   '          and action=\'SUBMIT\'),\n'
                   '       %s,\n'
                   '       now(),\n'
                   '       now(),\n'
                   '       now(),\n'
                   '       (select action_info\n'
                   '        from as_queue\n'
                   '        where task_id=%s\n'
                   '          and action=\'SUBMIT\');')
            sql_data = (task_id, task_id, new_status, task_id)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = True
            self.query_done(
                ("Status change for task '%s' "
                 "successfully changed to '%s'" % (task_id, new_status)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      serve_callback - Process an incoming callback call for a given task_id
    """

    def serve_callback(self, task_id, info):
        # Retrieve task record
        task_record = self.get_task_record(task_id)
        # Create a file containing callback_info
        # Callback info filename will be stored in action_info dir
        # and the file name will be: callback.task_id
        callback_filename = ''
        callback_f = None
        try:
            callback_filename = '%s/callback.%s' % (task_record['iosandbox'],
                                                    task_id)
            logging.debug('Creating callback info file: %s'
                          % callback_filename)
            logging.debug('Callback info content: \'%s\'' % json.dumps(info))
            callback_f = open(callback_filename, 'w')
            callback_f.write(json.dumps(info))
            callback_f.close()
        except IOError as xxx_todo_changeme:
            (errno, strerror) = xxx_todo_changeme.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        finally:
            if callback_f is not None:
                callback_f.close()
        # Add a queue recod informing the EI
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from as_queue\n'
                   'where task_id = %s\n'
                   '  and action = \'CALLBACK\';')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            callback_count = cursor.fetchone()
            if callback_count == 0:
                # 1st Callback entry
                sql = ('insert into as_queue (task_id,\n'
                       '                      target_id,\n'
                       '                      target,\n'
                       '                      action,\n'
                       '                      status,\n'
                       '                      target_status,\n'
                       '                      retry,\n'
                       '                      creation,\n'
                       '                      last_change,\n'
                       '                      check_ts,\n'
                       '                      action_info)\n'
                       'select task_id,\n'
                       '       target_id,\n'
                       '       target,\n'
                       '       \'CALLBACK\',\n'
                       '       \'DONE\',\n'
                       '       target_status,\n'
                       '       retry,\n'
                       '       now(),\n'
                       '       now(),\n'
                       '       now(),\n'
                       '       action_info\n'
                       'from as_queue\n'
                       ' where task_id = %s\n'
                       '   and action = \'SUBMIT\';')
            else:
                # next Callback entry
                sql = ('update as_queue\n'
                       'set last_change = now()\n'
                       'where task_id = %s\n'
                       'and action = \'CALLBACK\';')
            sql_data = (task_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            self.query_done(
                ("Callback for task '%s' successfully queued; info file: '%s'"
                 % (task_id, callback_filename)))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return

    #
    # Application
    #
    """
      app_exists - Return True if the given app_id exists, False otherwise
    """

    def app_exists(self, application):
        db = None
        cursor = None
        safe_transaction = False
        count = 0
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from application\n'
                   'where id = %s;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
            self.query_done(
                "App \'%s\' existing is %s" % (app_id, count > 0))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return count > 0

    """
      get_app_list - Get the list of applications
    """

    def get_app_list(self):
        db = None
        cursor = None
        safe_transaction = False
        app_ids = []
        try:
            # Get Task ids preparing the right query (user/app_id)
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql_data = ()
            sql = ('select id\n'
                   'from application\n'
                   'order by id asc;')
            logging.debug(sql % sql_data)
            cursor.execute(sql)
            for app_id in cursor:
                app_ids += [app_id[0], ]
            self.query_done(
                "Application list: '%s'" % app_ids)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_ids

    """
       get_app_record - Get application record from its id or name
    """

    def get_app_record(self, application):
        db = None
        cursor = None
        safe_transaction = False
        app_record = {}
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # application record
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,outcome\n'
                '      ,creation\n'
                '      ,enabled\n'
                'from application\n'
                'where id=%s;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_dbrec = cursor.fetchone()
            if app_dbrec is not None:
                app_dicrec = {
                    "id": app_dbrec[0],
                    "name": app_dbrec[1],
                    "description": app_dbrec[2],
                    "outcome": app_dbrec[3],
                    "creation": self.date_format(app_dbrec[4]),
                    "enabled": bool(app_dbrec[5])}
            else:
                self.query_done(
                    "Could not find application '%s'" % application)
                return {}
            # Application parameters
            app_id = app_dicrec['id']
            sql = ('select pname\n'
                   '      ,pvalue\n'
                   '      ,pdesc\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   'order by param_id asc;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_params = []
            for param in cursor:
                app_params += [{"name": param[0],
                                "value": param[1],
                                "description": param[2]}, ]
            # Application input files
            sql = ('select file\n'
                   '      ,path\n'
                   '      ,override\n'
                   'from application_file\n'
                   'where app_id=%s\n'
                   'order by file_id asc;')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            app_ifiles = []
            for ifile in cursor:
                ifile_entry = {
                    "name": ifile[0],
                    "path": ifile[1],
                    "override": bool(ifile[2])
                }
                # Downloadable application files
                # Add url field in case the path exists
                if ifile[1] is not None and len(ifile[1]) > 0:
                    ifile_entry['url'] = 'file?%s' % urllib.urlencode(
                        {"path": ifile[1],
                         "name": ifile[0]})
                app_ifiles += [ifile_entry, ]
            # Application infrastructures
            app_infras = self.get_infra_list(app_id)
            # sql = (
            #     'select id\n'
            #     '      ,name\n'
            #     '      ,description\n'
            #     '      ,creation,
            #     '      ,enabled\n'
            #     'from infrastructure\n'
            #     'where app_id=%s;')
            # sql_data = (app_id,)
            # logging.debug(sql % sql_data)
            # cursor.execute(sql, sql_data)
            # app_infras = []
            # for app_infra in cursor:
            #     app_infra_entry = {
            #         "id": str(app_infra[0]),
            # #       "name": app_infra[1],
            #         "description": app_infra[2],
            #         "creation": self.date_format(app_infra[3]),
            #         "enabled": bool(app_infra[4]),
            #         "virtual": False}
            ##        ,"parameters"     : []}
            #     app_infras += [app_infra_entry, ]
            # for app_infra in app_infras:
            #     sql = ('select pname\n'
            #            '      ,pvalue\n'
            #            'from infrastructure_parameter\n'
            #            'where infra_id=%s\n'
            #            'order by param_id asc;')
            #     sql_data = (app_infra['id'],)
            #     logging.debug(sql % sql_data)
            #     cursor.execute(sql, sql_data)
            #     infra_params = []
            #     for infra_param in cursor:
            #         infra_params += [{
            #             "name": infra_param[0], "value": infra_param[1]
            #         }, ]
            #     app_infra["parameters"] = infra_params

            # Prepare output
            app_record = {
                "id": str(app_id),
                "name": app_dicrec['name'],
                "description": app_dicrec['description'],
                "outcome": app_dicrec['outcome'],
                "creation": str(
                    app_dicrec['creation']),
                "enabled": app_dicrec['enabled'],
                "parameters": app_params,
                "files": app_ifiles,
                "infrastructures": app_infras}
            self.query_done("Application '%s' record: '%s'"
                            % (app_id, app_record))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_record

    """
      init_app - initialize an application
                 from the given parameters: name
                                           ,description
                                           ,enabled
                                           ,parameters
                                           ,inp_files
                                           ,infrastructures
    """

    def init_app(
            self,
            name,
            description,
            outcome,
            enabled,
            parameters,
            inp_files,
            files,
            infrastructures):
        # Start creating app
        db = None
        cursor = None
        safe_transaction = True
        try:
            # Insert new application record
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('insert into application (id\n'
                   '                        ,name\n'
                   '                        ,description\n'
                   '                        ,outcome\n'
                   '                        ,creation\n'
                   '                        ,enabled)\n'
                   'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
                   '      ,%s                              -- name\n'
                   '      ,%s                              -- description\n'
                   '      ,%s                              -- outcome\n'
                   '      ,now()                           -- creation\n'
                   '      ,%s                              -- enabled\n'
                   'from application;')
            sql_data = (name, description, outcome, enabled)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Get inserted application_id
            sql = 'select max(id) from application;'
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql)
            app_id = cursor.fetchone()[0]
            # Insert Application parameters
            if parameters is not []:
                for param in parameters:
                    sql = (
                        'insert into application_parameter (app_id\n'
                        '                                  ,param_id\n'
                        '                                  ,pname\n'
                        '                                  ,pvalue\n'
                        '                                  ,pdesc)\n'
                        'select %s                                          \n'
                        '      ,if(max(param_id) is NULL,1,max(param_id)+1) \n'
                        '      ,%s                                          \n'
                        '      ,%s                                          \n'
                        '      ,%s                                          \n'
                        'from application_parameter\n'
                        'where app_id=%s')
                    sql_data = (app_id,
                                param['name'],
                                param['value'],
                                param.get('description', None),
                                app_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            # Insert Application input_files
            for ifile in inp_files:
                sql = (
                    'insert into application_file (app_id\n'
                    '                            ,file_id\n'
                    '                            ,file\n'
                    '                            ,path\n'
                    '                            ,override)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    '      ,%s\n'
                    '      ,%s\n'
                    'from application_file\n'
                    'where app_id=%s')
                sql_data = (app_id,
                            ifile['name'],
                            ifile['path'],
                            ifile['override'],
                            app_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            # Insert Application files
            # Application files behave differently they have forced override
            # flag and do not have path information until application/input
            # API call is executed
            for app_file in files:
                sql = (
                    'insert into application_file (app_id\n'
                    '                            ,file_id\n'
                    '                            ,file\n'
                    '                            ,path\n'
                    '                            ,override)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    '      ,\'\'\n'
                    '      ,TRUE\n'
                    'from application_file\n'
                    'where app_id=%s')
                sql_data = (app_id, app_file, app_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            # Insert Application infrastructures
            # ! Infrastructures may be expressed by definition or by
            #   existing infrastructure ids
            for infra in infrastructures:
                if isinstance(infra, dict):
                    # Infrastructure description is provided
                    sql = ('insert into infrastructure (id\n'
                           '                           ,app_id\n'
                           '                           ,name\n'
                           '                           ,description\n'
                           '                           ,creation\n'
                           '                           ,enabled\n'
                           '                           ,vinfra\n'
                           '                           )\n'
                           'select if(max(id) is NULL,1,max(id)+1) \n'
                           '      ,%s                              \n'
                           '      ,%s                              \n'
                           '      ,%s                              \n'
                           '      ,now()                           \n'
                           '      ,%s                              \n'
                           '      ,%s                              \n'
                           'from infrastructure;'
                           )
                    sql_data = (app_id,
                                infra['name'],
                                infra['description'],
                                infra['enabled'],
                                infra['virtual']
                                )
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
                    # Get inserted infrastructure_id
                    sql = 'select max(id) from infrastructure;'
                    sql_data = ()
                    logging.debug(sql % sql_data)
                    cursor.execute(sql)
                    infra_id = cursor.fetchone()[0]
                    # Insert Application infrastructure parameters
                    for param in infra['parameters']:
                        sql = (
                            'insert into infrastructure_parameter (infra_id\n'
                            '                                     ,param_id\n'
                            '                                     ,pname\n'
                            '                                     ,pvalue\n'
                            '                                     ,pdesc)\n'
                            'select %s\n'
                            '      ,if(max(param_id) is NULL,\n'
                            '          1,max(param_id)+1) \n'
                            '      ,%s\n'
                            '      ,%s\n'
                            '      ,%s\n'
                            'from infrastructure_parameter\n'
                            'where infra_id = %s;')
                        sql_data = (infra_id,
                                    param['name'],
                                    param['value'],
                                    param.get('description', None),
                                    infra_id)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                else:
                    # Existing infrastructure id is provided
                    # Infrastructure may be already assigned or not
                    # If not yet assigned, just modify the app_id;
                    # otherwise copy the whole infrastructure
                    #
                    # infra_record = self.get_infra_record(infra)
                    #
                    # !!! I cannot use get_infra_record call due
                    #     to the transaction lost; infra record
                    #     must be taken within this transaction.
                    #     Needed values are:
                    #         app_id
                    #         name
                    #         description
                    #         enabled
                    #         virtual
                    #
                    sql = ('select app_id,\n'
                           '       name,\n'
                           '       description,\n'
                           '       enabled,\n'
                           '       vinfra\n'
                           'from infrastructure\n'
                           'where id=%s\n'
                           'order by 1 asc ,2 asc\n'
                           'limit 1;')
                    sql_data = (int(infra),)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
                    sql_record = cursor.fetchone()
                    infra_record = {'id': int(infra),
                                    'app_id': int(sql_record[0]),
                                    'name': sql_record[1],
                                    'description': sql_record[2],
                                    'enabled': bool(sql_record[3]),
                                    'virtual': bool(sql_record[4])}
                    if infra_record['app_id'] == 0:
                        # Unassigned infrastructure just requires to
                        # switch app_id from 0 to the current app_id
                        sql = ('update infrastructure set app_id = \'%s\'\n'
                               'where id = %s\n'
                               '  and app_id = 0;')
                        sql_data = (app_id, infra_record['id'])
                    else:
                        # Already assigned infrastructure requires a new
                        # entry in infrastructure table
                        sql = ('insert into infrastructure (id\n'
                               '                           ,app_id\n'
                               '                           ,name\n'
                               '                           ,description\n'
                               '                           ,creation\n'
                               '                           ,enabled\n'
                               '                           ,vinfra\n'
                               '                           )\n'
                               'values (%s    \n'
                               '       ,%s    \n'
                               '       ,%s    \n'
                               '       ,%s    \n'
                               '       ,now() \n'
                               '       ,%s    \n'
                               '       ,%s);')
                        sql_data = (int(infra_record['id']),
                                    app_id,
                                    infra_record['name'],
                                    infra_record['description'],
                                    infra_record['enabled'],
                                    infra_record['virtual']
                                    )
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            self.query_done(
                "Application successfully inserted with id '%s'" % app_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
            app_id = 0
        finally:
            self.close_db(db, cursor, safe_transaction)
        return app_id

    """
      insert_or_update_app_file - Insert or update the application files
    """

    def insert_or_update_app_file(self, application, file_name, file_path):
        db = None
        cursor = None
        safe_transaction = True
        status = False
        app_id = self.app_param_to_app_id(application)
        try:
            # Delete given application records
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from application_file\n'
                   'where app_id = %s\n'
                   '  and file = %s;')
            sql_data = (app_id, file_name)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
            if count > 0:
                sql = ('update application_file\n'
                       'set path = %s\n'
                       'where app_id = %s\n'
                       '  and file = %s;')
                sql_data = (file_path, app_id, file_name)
            else:
                sql = ('insert into application_file (app_id\n'
                       '                            ,file_id\n'
                       '                            ,file\n'
                       '                            ,path\n'
                       '                            ,override)\n'
                       'select %s                                          \n'
                       '      ,if(max(file_id) is NULL,1,max(file_id)+1)   \n'
                       '      ,%s                                          \n'
                       '      ,%s                                          \n'
                       '      ,TRUE                                        \n'
                       'from application_file\n'
                       'where app_id=%s')
                sql_data = (app_id, file_name, file_path, app_id)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            self.query_done(
                "insert or update of file '%s/%s' for app '%s'" % (file_path,
                                                                   file_name,
                                                                   app_id))
            status = True
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return status

    """
      app_delete - delete application with a given id
    """

    def app_delete(self, application):
        # Start deleting app
        db = None
        cursor = None
        safe_transaction = True
        result = False
        app_id = self.app_param_to_app_id(application)
        try:
            # Delete given application records
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            #
            # (!) Pay attention infrastructures belonging to
            #     different applications may share the same
            #    id (infra_id in parameters); a check is
            #    necessary here ...
            #
            sql = 'delete from fg_group_apps where app_id=%s;'
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = (
                'delete from infrastructure_parameter\n'
                'where infra_id in (select id\n'
                '                   from infrastructure\n'
                '                   where app_id=%s);')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = 'delete from infrastructure where app_id=%s;'
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = 'delete from application_file where app_id=%s;'
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = 'delete from application_parameter where app_id=%s;'
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = 'delete from application where id=%s;'
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            result = True
            self.query_done(
                "Application '%s' successfully deleted" % app_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      enable_app_by_userid - enable all groups owned by the given userid to
                             execute the specified application id
    """

    def enable_app_by_userid(self, user_id, app_id):
        db = None
        cursor = None
        safe_transaction = True
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # Task record
            sql = "select group_id from fg_user_group where user_id = %s"
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            group_ids = []
            for group_id_record in cursor:
                group_ids.append(group_id_record[0])
            for group_id in group_ids:
                sql = (
                    "insert into fg_group_apps (group_id, app_id, creation)\n"
                    "values (%s, %s, now())")
                sql_data = (group_id, app_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            self.query_done(
                "Application '%s' enabled for user '%s'" % (app_id,
                                                            user_id))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return None

    """
        infra_exists - Return True if the given infra_id exists,
                       False otherwise
    """

    def infra_exists(self, infra_id):
        db = None
        cursor = None
        safe_transaction = False
        count = 0
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from infrastructure\n'
                   'where id = %s;')
            sql_data = (infra_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
            self.query_done(
                "Infrastructure '%s' exists is: %s" % (infra_id, count > 0))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return count > 0

    """
      get_infra_list - Get the list of infrastructures; if app_id is not None
                       return the infrastructures used by the given application
    """

    def get_infra_list(self, application):
        db = None
        cursor = None
        safe_transaction = False
        infra_ids = []
        app_id = self.app_param_to_app_id(application)
        try:
            # Get Task ids preparing the right query (user/app_id)
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql_data = ()
            if app_id is None:
                sql = ('select distinct id\n'
                       'from infrastructure order by 1 asc;')
            else:
                sql = ('select id\n'
                       'from infrastructure\n'
                       'where app_id = %s order by id asc;')
                sql_data = (app_id,)
                logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for infra_id in cursor:
                infra_ids += [infra_id[0], ]
            self.query_done(
                "Infrastructure list for app '%s': '%s'" % (app_id,
                                                            infra_ids))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return infra_ids

    """
           get_infra_record - Get infrastructure record from its id
    """

    def get_infra_record(self, infra_id):
        db = None
        cursor = None
        safe_transaction = True
        infra_record = {}
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # infrastructure record
            sql = (
                'select app_id,\n'
                '       name,\n'
                '       description,\n'
                '       creation,\n'
                '       enabled,\n'
                '       vinfra\n'
                'from infrastructure\n'
                'where id=%s\n'
                'order by 1 asc ,2 asc\n'
                'limit 1;')
            sql_data = (infra_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            infra_dbrec = cursor.fetchone()
            if infra_dbrec is not None:
                infra_dicrec = {
                    "id": str(infra_id),
                    "app_id": str(infra_dbrec[0]),
                    "name": infra_dbrec[1],
                    "description": infra_dbrec[2],
                    "creation": self.date_format(infra_dbrec[3]),
                    "enabled": bool(infra_dbrec[4]),
                    "virtual": bool(infra_dbrec[5])}
            else:
                self.query_done(
                    "Could not find infrastructure '%s'" % infra_id)
                return {}
            # Infrastructure parameters
            sql = ('select pname\n'
                   '      ,pvalue\n'
                   '      ,pdesc\n'
                   'from infrastructure_parameter\n'
                   'where infra_id=%s\n'
                   'order by param_id asc;')
            sql_data = (infra_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            infra_params = []
            for param in cursor:
                infra_params += [
                    {"name": param[0],
                     "value": param[1],
                     "description": param[2]},
                ]
            # Prepare output
            infra_record = {
                "id": infra_dicrec['id'],
                "app_id": infra_dicrec['app_id'],
                "name": infra_dicrec['name'],
                "description": infra_dicrec['description'],
                "creation": infra_dicrec['creation'],
                "enabled": infra_dicrec['enabled'],
                "virtual": infra_dicrec['virtual'],
                "parameters": infra_params}
            self.query_done(
                "Infrastructure '%s': '%s'" % (infra_id, infra_record))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return infra_record

    """
      init_infra - initialize an infrastructure
                   from the given parameters: name
                                             ,description
                                             ,enabled
                                             ,vinfra
                                             ,infrastructure_parameters
    """

    def init_infra(
            self,
            name,
            description,
            enabled,
            vinfra,
            infrastructure_parameters):
        # Start creating app
        db = None
        cursor = None
        safe_transaction = True
        infra_id = -1
        try:
            # Insert new application record
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('insert into infrastructure (id\n'
                   '                           ,app_id\n'
                   '                           ,name\n'
                   '                           ,description\n'
                   '                           ,creation\n'
                   '                           ,enabled\n'
                   '                           ,vinfra\n'
                   '                           )\n'
                   'select if(max(id) is NULL,1,max(id)+1)\n'
                   '      ,0\n'
                   '      ,%s\n'
                   '      ,%s\n'
                   '      ,now()\n'
                   '      ,%s\n'
                   '      ,%s\n'
                   'from infrastructure;'
                   )
            sql_data = (name,
                        description,
                        enabled,
                        vinfra
                        )
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Get inserted infrastructure_id
            sql = 'select max(id) from infrastructure;'
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql)
            infra_id = cursor.fetchone()[0]
            # Insert Application infrastructure parameters
            for param in infrastructure_parameters:
                sql = ('insert into infrastructure_parameter (infra_id\n'
                       '                                     ,param_id\n'
                       '                                     ,pname\n'
                       '                                     ,pvalue\n'
                       '                                     ,pdesc)\n'
                       'select %s\n'
                       '      ,if(max(param_id) is NULL,\n'
                       '          1,max(param_id)+1) \n'
                       '      ,%s\n'
                       '      ,%s\n'
                       '      ,%s\n'
                       'from infrastructure_parameter\n'
                       'where infra_id = %s;')
                sql_data = (infra_id,
                            param['name'],
                            param['value'],
                            param.get('description', None),
                            infra_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            self.query_done(
                "Infrastructure successfully created with id '%s'" % infra_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return infra_id

    """
      infra_delete - delete infrastructure with a given infra_id
                     and/or app_id
                     app_orphan flag, when true allow to delete  the
                     infrastructure even if it is used by applications
    """

    def infra_delete(self, infra_id, application, app_orhpan=False):
        # Start deleting infrastructure
        db = None
        cursor = None
        safe_transaction = True
        result = False
        app_orphans = 0
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # Check for orphan applications
            if not app_orhpan:
                sql = (
                    'select count(*)\n'
                    'from application a\n'
                    '    ,infrastructure i\n'
                    'where i.app_id=a.id\n'
                    '  and a.id != 0\n'
                    '  and i.id = %s;')
                sql_data = (infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                app_orphans = int(cursor.fetchone()[0])
            if app_orphans > 0:
                self.err_msg = ('Infrastructure having id: \'%s\' '
                                'is actually used by one or more '
                                'applications; please check the '
                                'configuration' % (infra_id,))
                return result
            if app_id is not None:
                #
                # (!) What about RUNNING instances in queue table that
                #     are using the infrastructure?
                #
                sql = (
                    'select count(*)\n'
                    'from as_queue q\n'
                    '    ,task t\n'
                    '    ,application a\n'
                    '    ,infrastructure i\n'
                    'where i.app_id=a.id\n'
                    '  and t.app_id=a.id\n'
                    '  and q.task_id=t.id\n'
                    '  and t.app_id=a.id\n'
                    '  and q.status=\'RUNNING\'\n'
                    '  and a.id = %s and i.id = %s;')
                sql_data = (app_id, infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                task_count = int(cursor.fetchone()[0])
                if task_count > 0:
                    self.err_msg = ('Infrastructure having id: \'%s\' '
                                    'may be actually in use by application '
                                    'having id: \'%s\'; please check '
                                    'the queue table.' % (infra_id,
                                                          app_id))
                    return result
                #
                # (!)The app_id is specified; the action impacts
                #    only the specified application
                #
                sql = (
                    'delete from infrastructure_parameter\n'
                    'where infra_id in (select id \n'
                    '                   from infrastructure \n'
                    '                   where app_id=%s\n'
                    '                     and (select count(*)\n'
                    '                          from infrastructure\n'
                    '                          where id=%s)=1);')
                sql_data = (app_id, infra_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                sql = 'delete from infrastructure where app_id=%s;'
                sql_data = (app_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result = True
            else:
                #
                # (!) What about RUNNING instances in queue table that
                #     are using the infrastructure?
                #
                sql = (
                    'select count(*)\n'
                    'from as_queue q\n'
                    '    ,task t\n'
                    '    ,application a\n'
                    '    ,infrastructure i\n'
                    'where i.app_id=a.id\n'
                    '  and t.app_id=a.id\n'
                    '  and q.task_id=t.id\n'
                    '  and t.app_id=a.id\n'
                    '  and q.status=\'RUNNING\'\n'
                    '  and i.id = %s;')
                sql_data = (infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                task_count = int(cursor.fetchone()[0])
                if task_count > 0:
                    self.err_msg = ('Infrastructure having id: \'%s\' '
                                    'may be actually in use; please check '
                                    'the queue table.' % infra_id)
                    return result
                #
                # (!) The app_id is not specified; the action impacts
                #     all applications
                #
                sql = (
                    'delete from infrastructure_parameter\n'
                    'where infra_id=%s;')
                sql_data = (infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                #
                # (!) In the future here should be handled the
                #     infrastructure_task table
                #
                sql = 'delete from infrastructure where id=%s;'
                sql_data = (infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result = True
            self.query_done(
                "Infrastructure '%s' successfully deleted" % infra_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      infra_change(infra_id, infra_desc)
      Change infrastructure values of the given infrastructure id,
      accordingly to the values contained in infra_desc json
    """

    def infra_change(self, infra_id, infra_desc):
        db = None
        cursor = None
        safe_transaction = True
        result = False
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # Update infrastructure values
            sql = (
                'update infrastructure set\n'
                '    name=%s,\n'
                '    description=%s,\n'
                '    enabled=%s,\n'
                '    vinfra=%s\n'
                'where id=%s;')
            sql_data = (infra_desc['name'],
                        infra_desc['description'],
                        infra_desc['enabled'],
                        infra_desc['virtual'],
                        infra_id)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Now remove any existing parameter
            json_params = infra_desc.get('parameters', None)
            if json_params is not None:
                sql = (
                    'delete from infrastructure_parameter\n'
                    'where infra_id=%s;')
                sql_data = (infra_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                # Re-insert parameters
                for param in json_params:
                    sql = (
                        'insert into infrastructure_parameter\n'
                        '    (infra_id,\n'
                        '     param_id,\n'
                        '     pname,\n'
                        '     pvalue,\n'
                        '     pdesc)\n'
                        '    select %s,\n'
                        '           if(max(param_id) is NULL,\n'
                        '              1,max(param_id)+1),\n'
                        '           %s,\n'
                        '           %s,\n'
                        '           %s\n'
                        '    from infrastructure_parameter\n'
                        '    where infra_id=%s;')
                    sql_data = (infra_id,
                                param['name'],
                                param['value'],
                                param.get('description', None),
                                infra_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            result = True
            self.query_done(
                "Infrastructure having id: '%s' successfully changed"
                % infra_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      app_change(app_id, app_desc)
      Change applicaion values of the given application id
      accordingly to the given app_desc json
    """

    def app_change(self, application, app_desc):
        db = None
        cursor = None
        safe_transaction = True
        result = False
        app_id = self.app_param_to_app_id(application)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # Update infrastructure values
            sql = (
                'update application set\n'
                '    name=%s,\n'
                '    description=%s,\n'
                '    outcome=%s,\n'
                '    enabled=%s\n'
                'where id=%s;')
            sql_data = (app_desc['name'],
                        app_desc['description'],
                        app_desc['outcome'],
                        app_desc['enabled'],
                        app_id)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            # Get a list of existing application files
            app_files = []
            sql = (
                'select file, path\n'
                'from application_file\n'
                'where app_id = %s\n'
                '  and (path is not null or path != \'\');')
            sql_data = (app_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for app_file in cursor:
                app_record = {"name": app_file[0],
                              "path": app_file[1]}
                app_files += [app_record]
            logging.debug("Associated files for applciation %s:"
                          % app_files)
            # Process 'files'
            json_files = app_desc.get('files', None)
            if json_files is not None:
                # Now remove any existing application file
                sql = (
                    'delete from application_file\n'
                    'where app_id=%s;')
                sql_data = (app_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                # Re-insert files
                for app_file in json_files:
                    # Try to find path in previous application list
                    app_file_path = None
                    for prev_app_file in app_files:
                        if prev_app_file["name"] == app_file:
                            app_file_path = prev_app_file["path"]
                            app_files.remove(prev_app_file)
                            break
                    sql = (
                        'insert into application_file\n'
                        '    (app_id,\n'
                        '     file_id,\n'
                        '     file,\n'
                        '     path,\n'
                        '     override)\n'
                        '    select %s,\n'
                        '           if(max(file_id) is NULL,\n'
                        '              1,max(file_id)+1),\n'
                        '           %s,\n'
                        '           %s,\n'
                        '           TRUE\n'
                        '    from application_file\n'
                        '    where app_id=%s;')
                    sql_data = (app_id,
                                app_file,
                                app_file_path,
                                app_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            # Process 'input_files'
            json_input_files = app_desc.get('input_files', None)
            if json_input_files is not None:
                # Re-insert files with input_files statement
                for app_file in json_input_files:
                    # Try to locate the file in previous application list
                    for prev_app_file in app_files:
                        if prev_app_file["name"] == app_file["name"] \
                                and prev_app_file["path"] == app_file["path"]:
                            app_files.remove(prev_app_file)
                            break
                    sql = (
                        'insert into application_file\n'
                        '    (app_id,\n'
                        '     file_id,\n'
                        '     file,\n'
                        '     path,\n'
                        '     override)\n'
                        '    select %s,\n'
                        '           if(max(file_id) is NULL,\n'
                        '              1,max(file_id)+1),\n'
                        '           %s,\n'
                        '           %s,\n'
                        '           %s\n'
                        '    from application_file\n'
                        '    where app_id=%s;')
                    sql_data = (app_id,
                                app_file["name"],
                                app_file["path"],
                                app_file["override"],
                                app_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            # Process parameters
            json_params = app_desc.get('parameters', None)
            if json_params is not None:
                # Delete parameters
                sql = (
                    'delete from application_parameter\n'
                    'where app_id=%s;')
                sql_data = (app_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                # Re-insert parameters
                for app_param in json_params:
                    sql = (
                        'insert into application_parameter\n'
                        '    (app_id,\n'
                        '     param_id,\n'
                        '     pname,\n'
                        '     pvalue,\n'
                        '     pdesc)\n'
                        '    select %s,\n'
                        '           if(max(param_id) is NULL,\n'
                        '              1,max(param_id)+1),\n'
                        '           %s,\n'
                        '           %s,\n'
                        '           %s\n'
                        '    from application_parameter\n'
                        '    where app_id=%s;')
                    sql_data = (app_id,
                                app_param["name"],
                                app_param["value"],
                                app_param.get("description", None),
                                app_id)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
            # Process 'infrastructures'
            json_infras = app_desc.get('infrastructures', None)
            if json_infras is not None:
                # Get the list of current infrastructure ids
                app_infras = []
                sql = 'select id from infrastructure where app_id=%s;'
                sql_data = (app_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                for qrec in cursor:
                    app_infras += [qrec[0]]
                # Process json infrastructures
                for infra in json_infras:
                    if isinstance(infra, dict):
                        # Infrastructure is explicitly given
                        logging.error("Explicit infrastructure description "
                                      "inserting infrastructure: %s" % infra)
                        sql = ('insert into infrastructure (id\n'
                               '                           ,app_id\n'
                               '                           ,name\n'
                               '                           ,description\n'
                               '                           ,creation\n'
                               '                           ,enabled\n'
                               '                           ,vinfra\n'
                               '                           )\n'
                               'select if(max(id) is NULL,1,max(id)+1)\n'
                               '      ,%s\n'
                               '      ,%s\n'
                               '      ,%s\n'
                               '      ,now()\n'
                               '      ,%s\n'
                               '      ,%s\n'
                               'from infrastructure;')
                        sql_data = (app_id,
                                    infra['name'],
                                    infra['description'],
                                    infra['enabled'],
                                    infra['virtual'])
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                        # Get inserted infrastructure_id
                        sql = 'select max(id) from infrastructure'
                        sql_data = ()
                        logging.debug(sql % sql_data)
                        cursor.execute(sql)
                        new_infra_id = cursor.fetchone()[0]
                        for param in infra['parameters']:
                            sql = ('insert into infrastructure_parameter\n'
                                   '     (infra_id\n'
                                   '     ,param_id\n'
                                   '     ,pname\n'
                                   '     ,pvalue\n'
                                   '     ,pdesc)\n'
                                   'select %s\n'
                                   '      ,if(max(param_id) is NULL,\n'
                                   '          1,max(param_id)+1) \n'
                                   '      ,%s\n'
                                   '      ,%s\n'
                                   '      ,%s\n'
                                   'from infrastructure_parameter\n'
                                   'where infra_id = %s;')
                            sql_data = (new_infra_id,
                                        param['name'],
                                        param['value'],
                                        param.get('description', None),
                                        new_infra_id)
                            logging.debug(sql % sql_data)
                            cursor.execute(sql, sql_data)
                    else:
                        # Check if received infra id exists
                        infra = int(infra)
                        infra_found = False
                        for prev_infra in app_infras:
                            if prev_infra == infra:
                                infra_found = True
                                app_infras.remove(infra)
                                break
                        if infra_found is not True:
                            # Add the new infrastructure id
                            # Two cases; unassigned infra or already assigned
                            # infrastructure
                            sql = (
                                'select count(*)=1\n'
                                'from infrastructure\n'
                                'where app_id=0 and id=%s;')
                            sql_data = (infra,)
                            logging.debug(sql % sql_data)
                            cursor.execute(sql, sql_data)
                            unassign_state = bool(cursor.fetchone()[0])
                            if unassign_state is True:
                                # Unassigned infrastructures need an update
                                logging.debug(
                                    "Infrastructure %s is not yet assigned"
                                    % infra)
                                sql = (
                                    'update infrastructure\n'
                                    'set app_id = %s\n'
                                    'where id = %s and app_id = 0;')
                                sql_data = (app_id, infra)
                            else:
                                # Assigned infrastructures can be added
                                logging.debug(
                                    "Infrastructure %s is already assigned"
                                    % infra)
                                sql = (
                                    'insert into infrastructure\n'
                                    '    (id,\n'
                                    '     app_id,\n'
                                    '     name,\n'
                                    '     description,\n'
                                    '     creation,\n'
                                    '     enabled,\n'
                                    '     vinfra)\n'
                                    'select %s,\n'
                                    '       %s,\n'
                                    '       (select name\n'
                                    '        from infrastructure\n'
                                    '        where id = %s\n'
                                    '        limit 1),\n'
                                    '       (select description\n'
                                    '        from infrastructure\n'
                                    '        where id = %s\n'
                                    '        limit 1),\n'
                                    '       now(),\n'
                                    '       TRUE,\n'
                                    '       (select vinfra\n'
                                    '        from infrastructure\n'
                                    '        where id = %s\n'
                                    '        limit 1);')
                                sql_data = (infra,
                                            app_id,
                                            infra,
                                            infra,
                                            infra)
                            # Execute the SQL statement
                            logging.debug(sql % sql_data)
                            cursor.execute(sql, sql_data)
                        else:
                            logging.debug("Infrastructure '%s' already "
                                          "exists in application '%s'"
                                          % (infra, app_id))
                # Remove remaining infrastructures no more specified only
                # if the infrastructure is assinged only to this application
                for infra in app_infras:
                    sql = ('select count(*)=1\n'
                           'from infrastructure\n'
                           'where id=%s;')
                    sql_data = (infra,)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
                    del_infra = bool(cursor.fetchone()[0])
                    if del_infra is True:
                        # Infrastructure will be not removed but placed in
                        # unassigned status (app_id == 0)
                        logging.debug("Infrastructure %s is assigned only "
                                      "to application %s" % (infra, app_id))
                        sql = ('update infrastructure\n'
                               'set app_id = 0\n'
                               'where id=%s\n'
                               '  and app_id=%s;')
                        sql_data = (infra,
                                    app_id)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                    else:
                        logging.debug("Infrastructure %s is not only "
                                      "assigned to application %s" %
                                      (infra, app_id))
                        sql = ('delete from infrastructure\n'
                               'where id=%s\n'
                               '  and app_id=%s;')
                        sql_data = (infra,
                                    app_id)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
            # Remove from the filesystem the list of remaining files
            for prev_app_file in app_files:
                prev_app_file_path = ("%s/%s" % (prev_app_file["path"],
                                                 prev_app_file["name"]))
                try:
                    os.remove(prev_app_file_path)
                    logging.debug("Successfully removed file: '%s'"
                                  % prev_app_file_path),
                except OSError:
                    logging.error("Unable to remove file: '%s'"
                                  % prev_app_file_path)
                # Unregister file from application_file
                sql = ('delete from application_file\n'
                       'where app_id = %s\n'
                       '  and file= %s\n'
                       '  and path = %s;')
                sql_data = (app_id,
                            prev_app_file["name"],
                            prev_app_file["path"])
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            result = True
            self.query_done(
                "Application having id '%s' successfully changed"
                % app_id)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    #
    # User
    #

    """
      user_exists - Return True if the given user exists, False otherwise
    """

    def user_exists(self, user):
        db = None
        cursor = None
        safe_transaction = False
        count = 0
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from fg_user\n'
                   'where id=%s;')
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
            self.query_done(
                "User \'%s\' existing is %s" % (user, count > 0))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return count > 0

    """
      users_retrieve - Retrieve all user records from database
    """

    def users_retrieve(self):
        db = None
        cursor = None
        safe_transaction = False
        result = []
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id,\n'
                   '       name,\n'
                   '       first_name,\n'
                   '       last_name,\n'
                   '       institute,\n'
                   '       mail,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_user\n')
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for record in cursor:
                result += [{
                    'id': record[0],
                    'name': record[1],
                    'first_name': record[2],
                    'last_name': record[3],
                    'institute': record[4],
                    'mail': record[5],
                    'creation': self.date_format(record[6]),
                    'modified': self.date_format(record[7]), }]
            self.query_done(
                "Loaded %s users" % len(result))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      user_retrieve - Retrieve user record from database
    """

    def user_retrieve(self, user):
        db = None
        cursor = None
        safe_transaction = False
        result = None
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id,\n'
                   '       name,\n'
                   '       first_name,\n'
                   '       last_name,\n'
                   '       institute,\n'
                   '       mail,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_user\n'
                   'where id=%s;')
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            if record is not None:
                result = {
                    'id': record[0],
                    'name': record[1],
                    'first_name': record[2],
                    'last_name': record[3],
                    'institute': record[4],
                    'mail': record[5],
                    'creation': self.date_format(record[6]),
                    'modified': self.date_format(record[7]), }
            self.query_done(
                "User \'%s\' values: %s" % (user, result))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
        user_create - Create a user from given user data
    """

    def user_create(self, user_data):
        # Start creating app
        db = None
        cursor = None
        safe_transaction = True
        result = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            # First check if the user already exists
            sql = ('select count(*)\n'
                   'from fg_user\n'
                   'where name = %s\n'
                   '   or mail = %s;')
            sql_data = (user_data['name'],
                        user_data['mail'])
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
            if count == 0:
                # Insert the new user only if it does not exist
                sql = ('insert into fg_user (id\n'
                       '                    ,name\n'
                       '                    ,first_name\n'
                       '                    ,last_name\n'
                       '                    ,institute\n'
                       '                    ,mail\n'
                       '                    ,password\n'
                       '                    ,creation\n'
                       '                    ,modified\n'
                       '                    ,enabled\n'
                       '                    )\n'
                       'select if(max(id) is NULL,1,max(id)+1)\n'
                       '      ,%s\n'
                       '      ,%s\n'
                       '      ,%s\n'
                       '      ,%s\n'
                       '      ,%s\n'
                       '      ,\'\'\n'
                       '      ,now()\n'
                       '      ,now()\n'
                       '      ,true\n'
                       'from fg_user;'
                       )
                sql_data = (user_data['name'],
                            user_data['first_name'],
                            user_data['last_name'],
                            user_data['institute'],
                            user_data['mail'],)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
            # Get inserted record
            sql = ('select id,\n'
                   '       name,\n'
                   '       first_name,\n'
                   '       last_name,\n'
                   '       institute,\n'
                   '       mail,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_user\n'
                   'where name = %s;')
            sql_data = (user_data['name'],)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            result = {
                'id': record[0],
                'name': record[1],
                'first_name': record[2],
                'last_name': record[3],
                'institute': record[4],
                'mail': record[5],
                'creation': self.date_format(record[6]),
                'modified': self.date_format(record[7]), }
            self.query_done(
                "User with name: '%s' successfully created, with id: %s"
                % (result['name'], result['id']))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
          user_data - Retrieve user data records from database
    """

    def user_data(self, user):
        db = None
        cursor = None
        safe_transaction = False
        data = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select ud.data_id,\n'
                   '       ud.data_name,\n'
                   '       ud.data_value,\n'
                   '       ud.data_desc,\n'
                   '       ud.data_proto,\n'
                   '       ud.data_type,\n'
                   '       ud.creation,\n'
                   '       ud.last_change\n'
                   'from fg_user_data ud\n'
                   'where ud.user_id=%s\n'
                   '  and ud.data_id = (select max(data_id)\n'
                   '                    from fg_user_data\n'
                   '                    where user_id=ud.user_id\n'
                   '                      and data_name=ud.data_name);')
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for user_data in cursor:
                if user_data is not None:
                    data_entry = {
                        'data_id': user_data[0],
                        'data_name': user_data[1],
                        'data_value': user_data[2],
                        'data_desc': user_data[3],
                        'data_proto': user_data[4],
                        'data_type': user_data[5],
                        'creation': self.date_format(user_data[6]),
                        'last_change': self.date_format(user_data[7]), }
                    data.append(data_entry)
            self.query_done(
                "User \'%s\' data: %s" % (user, data))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return data

    """
       user_data_name - Retrieve user data record having given data name from
                        database
    """

    def user_data_name(self, user, data_name):
        db = None
        cursor = None
        safe_transaction = False
        data = {}
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select ud.data_id,\n'
                   '       ud.data_name,\n'
                   '       ud.data_value,\n'
                   '       ud.data_desc,\n'
                   '       ud.data_proto,\n'
                   '       ud.data_type,\n'
                   '       ud.creation,\n'
                   '       ud.last_change\n'
                   'from fg_user_data ud\n'
                   'where ud.user_id=%s\n'
                   '  and ud.data_id=(select max(data_id)\n'
                   '                  from fg_user_data\n'
                   '                  where user_id=ud.user_id\n'
                   '                    and data_name=ud.data_name)\n'
                   '  and ud.data_name=%s;')
            sql_data = (user_id, data_name)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            data_entry = cursor.fetchone()
            if data_entry is not None:
                data = {
                    'data_id': data_entry[0],
                    'data_name': data_entry[1],
                    'data_value': data_entry[2],
                    'data_desc': data_entry[3],
                    'data_proto': data_entry[4],
                    'data_type': data_entry[5],
                    'creation': self.date_format(data_entry[6]),
                    'last_change': self.date_format(data_entry[7]), }
            self.query_done(
                "User \'%s\' data: %s" % (user, data))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return data

    """
       delete_user_data - Delete the given data records to the given user
    """

    def delete_user_data(self, user, data_entries):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for data in data_entries:
                sql = ('delete from fg_user_data\n'
                       'where user_id=%s\n'
                       '  and data_name=%s;')
                sql_data = (user_id,
                            data.get('data_name', ''))
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result += [data, ]
            self.query_done(
                "deleted data '%s' for user '%s'" %
                (result, user))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
        modify_user_data - Modify the given data records to the given user
    """

    def modify_user_data(self, user, data_entries):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for data in data_entries:
                sql = ('select max(data_id)\n'
                       'from fg_user_data\n'
                       'where user_id=%s\n'
                       '  and data_name=%s;')
                sql_data = (user_id,
                            data.get('data_name', ''))
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                max_data_id = cursor.fetchone()[0]
                logging.debug("max_data_id: %s" % max_data_id)
                sql = ('update fg_user_data\n'
                       'set data_value = %s,\n'
                       '    data_desc = %s,\n'
                       '    data_proto = %s,\n'
                       '    data_type = %s,\n'
                       '    last_change = now()\n'
                       'where user_id=%s\n'
                       '  and data_id=%s\n'
                       '  and data_name=%s;')
                sql_data = (data.get('data_value', ''),
                            data.get('data_desc', ''),
                            data.get('data_proto', ''),
                            data.get('data_type', ''),
                            user_id,
                            max_data_id,
                            data.get('data_name', ''))
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result += [data, ]
            self.query_done(
                "modified data '%s' for user '%s'" %
                (result, user))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
        add_user_data - Add a given data record to a given user
    """

    def add_user_data(self, user, data_entries):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for data in data_entries:
                sql = ('insert into fg_user_data (user_id,\n'
                       '                          data_id,\n'
                       '                          data_name,\n'
                       '                          data_value,\n'
                       '                          data_desc,\n'
                       '                          data_proto,\n'
                       '                          data_type,\n'
                       '                          creation,\n'
                       '                          last_change)\n'
                       'select %s,\n'
                       '       (select if(max(data_id) is NULL,\n'
                       '                  1,\n'
                       '                  max(data_id)+1)\n'
                       '        from fg_user_data\n'
                       '        where user_id = %s\n'
                       '          and data_name = %s),\n'
                       '       %s,\n'
                       '       %s,\n'
                       '       %s,\n'
                       '       %s,\n'
                       '       %s,\n'
                       '       now(),\n'
                       '       now();')
                sql_data = (user_id,
                            user_id,
                            data.get('data_name', ''),
                            data.get('data_name', ''),
                            data.get('data_value', ''),
                            data.get('data_desc', ''),
                            data.get('data_proto', ''),
                            data.get('data_type', ''))
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result += [data, ]
            self.query_done(
                "Inserted data '%s' for user '%s'" %
                (result, user))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
       groups_retrieve - Retrieve groups from database
    """

    def groups_retrieve(self):
        db = None
        cursor = None
        safe_transaction = False
        groups = []
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id,\n'
                   '       name,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_group;')
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for group_record in cursor:
                groups += [
                    {"id": group_record[0],
                     "name": group_record[1],
                     "creation": self.date_format(group_record[2]),
                     "modified": self.date_format(group_record[3]), }]
            self.query_done(
                "Groups: %s" % groups)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return groups

    """
      user_groups_retrieve - Retrieve user groups from database
    """

    def user_groups_retrieve(self, user):
        db = None
        cursor = None
        safe_transaction = False
        groups = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select g.id,\n'
                   '       g.name,\n'
                   '       g.creation,\n'
                   '       g.modified\n'
                   'from fg_group g,\n'
                   '     fg_user_group ug,\n'
                   '     fg_user u\n'
                   'where u.id = %s\n'
                   '  and u.id = ug.user_id\n'
                   '  and g.id = ug.group_id;')
            sql_data = (user_id,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for group_record in cursor:
                groups += [
                    {"id": group_record[0],
                     "name": group_record[1],
                     "creation": self.date_format(group_record[2]),
                     "modified": self.date_format(group_record[3]), }]
            self.query_done(
                "User groups for user name '%s': %s" % (user, groups))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return groups

    """
      group_retrieve - Retrieve group from database by name or id
    """

    def group_retrieve(self, group):
        db = None
        cursor = None
        safe_transaction = False
        result = None
        group_id = self.group_param_to_group_id(group)
        if group_id is not None:
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                sql = ('select id,\n'
                       '       name,\n'
                       '       creation,\n'
                       '       modified\n'
                       'from fg_group\n'
                       'where id=%s;')
                sql_data = (group_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                group_record = cursor.fetchone()
                if group_record is not None:
                    result = {
                        "id": group_record[0],
                        "name": group_record[1],
                        "creation": self.date_format(group_record[2]),
                        "modified": self.date_format(group_record[3]), }
                self.query_done(
                    "Group: %s" % result)
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
        return result

    """
      group_apps_retrieve - Return the list of applications associated to the
                            given group
    """

    def group_apps_retrieve(self, group):
        db = None
        cursor = None
        safe_transaction = False
        result = None
        applications = []
        group_id = self.group_param_to_group_id(group)
        if group_id is not None:
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                sql = ('select a.id,\n'
                       '       a.name,\n'
                       '       a.description,\n'
                       '       a.outcome,\n'
                       '       a.creation,\n'
                       '       a.enabled\n'
                       'from fg_group_apps ga,\n'
                       '      application a\n'
                       'where group_id=%s\n'
                       '  and ga.app_id=a.id;')
                sql_data = (group_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                for app_record in cursor:
                    applications += [
                        {"id": app_record[0],
                         "name": app_record[1],
                         "description": app_record[2],
                         "outcome": app_record[3],
                         "creation": self.date_format(app_record[4]),
                         "enabled": app_record[5], }]
                result = {"applications": applications}
                self.query_done(
                    "Applications: %s" % result)
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
        return result

    """
      group_apps_add - Add the given list of applications to the given group
    """

    def group_apps_add(self, group, app_ids):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        group_id = self.group_param_to_group_id(group)
        if group_id is not None:
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                for app_id in app_ids:
                    sql = 'select count(*)>0 from application where id = %s;'
                    sql_data = (app_id,)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
                    app_exists = cursor.fetchone()
                    if app_exists > 0:
                        sql = ('insert into fg_group_apps (group_id,\n'
                               '                           app_id,\n'
                               '                           creation)\n'
                               'values (%s, %s, now());')
                        sql_data = (group_id, app_id,)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                        result += [app_id, ]
                self.query_done(
                    "Applications %s, added to group: %s" % (result, group))
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
        return result

    """
      group_add - Add a given group
    """

    def group_add(self, group_name):
        db = None
        cursor = None
        safe_transaction = True
        result = None
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('insert into fg_group (id, name, creation, modified)\n'
                   'select if(max(id) is NULL,1,max(id)+1),\n'
                   '       %s,\n'
                   '       now(),\n'
                   '       now()\n'
                   'from fg_group;')
            sql_data = (group_name,)
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            sql = ('select id,\n'
                   '       name,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_group\n'
                   'where name = %s')
            sql_data = (group_name,)
            logging.debug(sql, sql_data)
            cursor.execute(sql, sql_data)
            group_record = cursor.fetchone()
            if (group_record is not None and
                    group_name == group_record[1]):
                result = {
                    "id": group_record[0],
                    "name": group_record[1],
                    "creation": self.date_format(group_record[2]),
                    "modified": self.date_format(group_record[3]), }
            else:
                result = None
            self.query_done(
                "Group: %s successfully created" % group_name)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      add_user_groups - Assign to the given user, the given list of groups
    """

    def add_user_groups(self, user, gnames_or_ids):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for group in gnames_or_ids:
                group_id = self.group_param_to_group_id(group)
                sql = ('insert into fg_user_group (user_id,\n'
                       '                           group_id,\n'
                       '                           creation)\n'
                       'select u.id, g.id, now()\n'
                       'from fg_user u,\n'
                       'fg_group g\n'
                       'where u.id=%s\n'
                       '  and g.id=%s\n'
                       '  and (select count(*)\n'
                       '       from fg_user u1,\n'
                       '            fg_group g1,\n'
                       '            fg_user_group ug1\n'
                       '       where u1.id=%s\n'
                       '         and g1.id=%s\n'
                       '         and ug1.user_id=u1.id\n'
                       '         and ug1.group_id=g1.id) = 0;')
                sql_data = (user_id, group_id, user_id, group_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result += [group, ]
            self.query_done(
                "Inserted groups '%s' for user '%s'" %
                (result, user))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      delete_user_groups - Delete the given groups to the given user
    """

    def delete_user_groups(self, user, gnames_or_ids):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        user_id = self.user_param_to_user_id(user)
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            for group in gnames_or_ids:
                group_id = self.group_param_to_group_id(group)
                sql = ('delete from fg_user_group\n'
                       'where user_id=%s\n'
                       '  and group_id=%s;')
                sql_data = (user_id, group_id)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                result += [group, ]
            self.query_done(
                "deleted groups '%s' for user '%s'" %
                (result, user))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return result

    """
      user_tasks_retrieve - Retrieve ids of user tasks from database and
                            optionally an application name or id to filter
                            output
    """

    def user_tasks_retrieve(self, user, application):
        db = None
        cursor = None
        safe_transaction = False
        tasks = []
        user_id = self.user_param_to_user_id(user)
        app_id = self.app_param_to_app_id(application)
        sql, sql_data = (), ()

        if app_id is not None:
            sql = ('select t.id\n'
                   'from task t,\n'
                   '     fg_user u,\n'
                   '     application a\n'
                   'where u.id=%s\n'
                   '  and a.id=%s\n'
                   '  and t.status != \'PURGED\'\n'
                   '  and t.user=u.name\n'
                   '  and t.app_id=a.id\n'
                   'order by t.id desc;')
            sql_data = (user_id, app_id)
        else:
            sql = ('select t.id\n'
                   'from task t,\n'
                   '     fg_user u,\n'
                   '     application a\n'
                   'where u.id=%s\n'
                   '  and t.status != \'PURGED\'\n'
                   '  and t.user=u.name\n'
                   '  and t.app_id=a.id\n'
                   'order by t.id desc;')
            sql_data = (user_id)

        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for task in cursor:
                tasks += [task, ]
            self.query_done(
                "Tasks for user '%s': %s" % (user_id, tasks))
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return tasks

    """
      group_roles_retrieve - Return the list of roles associated to the
                             given group
    """

    def group_roles_retrieve(self, group):
        db = None
        cursor = None
        safe_transaction = False
        result = None
        roles = []
        group_id = self.group_param_to_group_id(group)
        if group_id is not None:
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                sql = ('select r.id,\n'
                       '       r.name,\n'
                       '       r.creation,\n'
                       '       r.modified\n'
                       'from fg_group_role gr,\n'
                       '     fg_role r\n'
                       'where gr.group_id = %s\n'
                       '  and gr.role_id = r.id;')
                sql_data = (group_id,)
                logging.debug(sql % sql_data)
                cursor.execute(sql, sql_data)
                for role_record in cursor:
                    roles += [
                        {"id": role_record[0],
                         "name": role_record[1],
                         "creation": self.date_format(role_record[2]),
                         "modified": self.date_format(role_record[3]), }]
                result = {"roles": roles}
                self.query_done(
                    "Roles: %s" % result)
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
        return result

    """
          group_roles_add - Add the given list of roles to the given group
    """

    def group_roles_add(self, group, role_ids):
        db = None
        cursor = None
        safe_transaction = True
        result = []
        group_id = self.group_param_to_group_id(group)
        if group_id is not None:
            try:
                db = self.connect(safe_transaction)
                cursor = db.cursor()
                for role_id in role_ids:
                    sql = 'select count(*)>0 from fg_role where id = %s;'
                    sql_data = (role_id,)
                    logging.debug(sql % sql_data)
                    cursor.execute(sql, sql_data)
                    role_exists = cursor.fetchone()
                    if role_exists > 0:
                        sql = ('insert into fg_group_role (group_id,\n'
                               '                           role_id,\n'
                               '                           creation)\n'
                               'values (%s, %s, now());')
                        sql_data = (group_id, role_id,)
                        logging.debug(sql % sql_data)
                        cursor.execute(sql, sql_data)
                        result += [role_id, ]
                self.query_done(
                    "Role %s, added to group: %s" % (result, group))
            except mysql.connector.Error as e:
                self.catch_db_error(e, db, safe_transaction)
            finally:
                self.close_db(db, cursor, safe_transaction)
        return result

    """
      roles_retrieve - Retrieve roles from database
    """

    def roles_retrieve(self):
        db = None
        cursor = None
        safe_transaction = False
        roles = []
        try:
            db = self.connect(safe_transaction)
            cursor = db.cursor()
            sql = ('select id,\n'
                   '       name,\n'
                   '       creation,\n'
                   '       modified\n'
                   'from fg_role;')
            sql_data = ()
            logging.debug(sql % sql_data)
            cursor.execute(sql, sql_data)
            for role_record in cursor:
                roles += [
                    {"id": role_record[0],
                     "name": role_record[1],
                     "creation": self.date_format(role_record[2]),
                     "modified": self.date_format(role_record[3]), }]
            self.query_done(
                "Roles: %s" % roles)
        except mysql.connector.Error as e:
            self.catch_db_error(e, db, safe_transaction)
        finally:
            self.close_db(db, cursor, safe_transaction)
        return roles
