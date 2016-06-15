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
__author__     = "Riccardo Bruno"
__copyright__  = "2015"
__license__    = "Apache"
__version__    = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

"""
  GridEngine API Server engine
"""
from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from flask_login import LoginManager, UserMixin, login_required, current_user
from Crypto.Cipher import ARC4
from OpenSSL import SSL
from werkzeug import secure_filename
from fgapiserver_db import fgapiserver_db
from fgapiserver_cfg import fgapiserver_cfg
import os
import sys
import uuid
import time
import json
import ConfigParser
import base64
import logging
import logging.config

# setup path
fgapirundir=os.path.dirname(os.path.abspath(__file__))+'/'
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir+'fgapiserver.conf'

# Load configuration
fg_config = fgapiserver_cfg(fgapiserver_config_file)

# fgapiserver settings
fgapiver            =     fg_config.getConfValue('fgapiver')
fgapiserver_name    =     fg_config.getConfValue('fgapiserver_name')
fgapisrv_host       =     fg_config.getConfValue('fgapisrv_host')
fgapisrv_port       = int(fg_config.getConfValue('fgapisrv_port'))
fgapisrv_debug      =    (fg_config.getConfValue('fgapisrv_debug').lower() == 'true')
fgapisrv_iosandbox  =     fg_config.getConfValue('fgapisrv_iosandbox')
fgapisrv_geappid    = int(fg_config.getConfValue('fgapisrv_geappid'))
fgjson_indent       = int(fg_config.getConfValue('fgjson_indent'))
fgapisrv_key        =     fg_config.getConfValue('fgapisrv_key')
fgapisrv_crt        =     fg_config.getConfValue('fgapisrv_crt')
fgapisrv_logcfg     =     fg_config.getConfValue('fgapisrv_logcfg')
fgapisrv_dbver      =     fg_config.getConfValue('fgapisrv_dbver')
fgapisrv_secret     =     fg_config.getConfValue('fgapisrv_secret')
fgapisrv_notoken    =    (fg_config.getConfValue('fgapisrv_notoken').lower() == 'true')
fgapisrv_notokenusr =     fg_config.getConfValue('fgapisrv_notokenusr')

# fgapiserver database settings
fgapisrv_db_host =     fg_config.getConfValue('fgapisrv_db_host')
fgapisrv_db_port = int(fg_config.getConfValue('fgapisrv_db_port'))
fgapisrv_db_user =     fg_config.getConfValue('fgapisrv_db_user')
fgapisrv_db_pass =     fg_config.getConfValue('fgapisrv_db_pass')
fgapisrv_db_name =     fg_config.getConfValue('fgapisrv_db_name')

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)
logger.debug(fg_config.showConf())

# setup Flask app
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

##
## flask-login User Class
##
class User(UserMixin):

    name = ''

    def __init__(self,id,name):
        self.id=id
        self.name=name
        print "id: '%s' - name: '%s'" % (id,name)

    def getId(self):
        return self.id

    def getName(self):
        return self.name


##
## Helper functions
##

# database versioning check
def checkDbVer():
    # Connect database
    fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                ,db_port=fgapisrv_db_port
                                ,db_user=fgapisrv_db_user
                                ,db_pass=fgapisrv_db_pass
                                ,db_name=fgapisrv_db_name
                                ,iosandbbox_dir=fgapisrv_iosandbox
                                ,fgapiserverappid=fgapisrv_geappid)
    fgapisrv_db.test()
    db_state=fgapisrv_db.getState()
    if db_state[0] != 0:
        # Couldn't contact database
        print "Unable to connect to the database!"
        sys.exit(1)
    else:
        # getDBVersion
        dbVer = fgapisrv_db.getDbVer()
        if fgapisrv_dbver is None or fgapisrv_dbver == '' or fgapisrv_dbver != dbVer:
            print "Current database version '%s' is not compatible with this version of the API server front-end; version %s is required" % (dbVer,fgapisrv_dbver)
            print "It is suggested to update your database applying new available patches"
            sys.exit(1)

# paginate the incoming response json vector, accordinlgly to page and per_page values
def paginate_response(response,page,per_page):
    # page in range [0..(len(task_response)/per_page)-1)]
    if page is not None and per_page is not None:
        pg=int(page)
        ppg=int(per_page)
        return response[pg*ppg:(pg+1)*ppg]
    else:
        return response

# Return the application id associated to the given task_id
def getTaskAppId(task_id):
    fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                ,db_port=fgapisrv_db_port
                                ,db_user=fgapisrv_db_user
                                ,db_pass=fgapisrv_db_pass
                                ,db_name=fgapisrv_db_name
                                ,iosandbbox_dir=fgapisrv_iosandbox
                                ,fgapiserverappid=fgapisrv_geappid)
    db_state=fgapisrv_db.getState()
    if db_state[0] == 0:
        # verifySessionToken returns user_id, usern_name associated to the
        # session token
        return fgapisrv_db.getTaskInfo(task_id)['application']['id']
    return None

# Return the task id associated to the file name and output
def getFileTaskId(file_name, file_path):
    fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                ,db_port=fgapisrv_db_port
                                ,db_user=fgapisrv_db_user
                                ,db_pass=fgapisrv_db_pass
                                ,db_name=fgapisrv_db_name
                                ,iosandbbox_dir=fgapisrv_iosandbox
                                ,fgapiserverappid=fgapisrv_geappid)
    db_state=fgapisrv_db.getState()
    if db_state[0] == 0:
        # verifySessionToken returns user_id, usern_name associated to the
        # session token
        return fgapisrv_db.getFileTaskId(file_name,file_path)
    return None



# verifySessionToken verifies the given session token returning user id and its name
#                    user id and name will be later used to retrieve user priviledges
#
# (!) Override this method to manage more complex and secure algorithms;
#
def verifySessionToken(sestoken):
    fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                ,db_port=fgapisrv_db_port
                                ,db_user=fgapisrv_db_user
                                ,db_pass=fgapisrv_db_pass
                                ,db_name=fgapisrv_db_name
                                ,iosandbbox_dir=fgapisrv_iosandbox
                                ,fgapiserverappid=fgapisrv_geappid)
    db_state=fgapisrv_db.getState()
    if db_state[0] == 0:
        # verifySessionToken returns user_id, usern_name associated to the
        # session token
        return fgapisrv_db.verifySessionToken(sestoken)
    return None

# processLogToken retrieve username and password from a given login token
#
# (!)Override this method to manage more complex and secure algorithms;
#    tester code uses the following encrypted string to store user credentials:
#        username=<username>:password=<password>:timestamp=<timestamp>
#
#    To create such log tokens, please use the following python snippet:
#
#    from Crypto.Cipher import ARC4
#    import time
#    import base64
#    secret = "0123456789ABCDEF" # (!) Please use fgapiserver_secret value
#    username = "<username>"
#    password = "<password>"
#    # Encode
#    obj=ARC4.new(secret)
#    b64em = base64.b64encode(obj.encrypt("username=%s:password=%s:timestamp=%s" % (username,password,int(time.time()))))
#    print b64em
#    # Decode
#    obj=ARC4.new(secret)
#    creds = obj.decrypt(base64.b64decode(b64em))
#    print creds
#
def processLogToken(logtoken):
    username=""
    password=""
    timestamp=0
    obj=ARC4.new(fgapisrv_secret)
    creds = obj.decrypt(base64.b64decode(logtoken))
    credfields = creds.split(":")
    if len(credfields)>0:
        username   = credfields[0].split("=")[1]
        password   = credfields[1].split("=")[1]
        timestamp  = credfields[2].split("=")[1]
    return username,password,timestamp

# createSessionToken accepts login tokens or username/password credentials returning an access token
def createSessionToken(**kwargs):
    timestamp= int(time.time())
    sestoken = ""
    logtoken = kwargs.get("logtoken","")
    username = kwargs.get("username","")
    password = kwargs.get("password","")
    if len(logtoken)>0:
        # Calculate credentials starting from a logtoken
        username, password, timestamp = processLogToken(logtoken)
    if len(username)>0 and len(password)>0:
        # Create a new access token starting from given username and password (DBRequired)
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] == 0:
            sestoken=fgapisrv_db.createSessionToken(username,password,timestamp)
    return sestoken

# authorizeUser This function returns true if the given user is authorized to process the requested action
#               The request will be checked against user group roles stored in the database
#
# Input: current_user - The user requesting the action
#        app_id       - The application id (if appliable)
#        user         - The user specified by the filter
#        reqrole      - The requested role: task_view, app_run, ...
#
def authorizeUser(current_user,app_id,user,reqrole):
    # Return True if token management is disabled
    if fgapisrv_notoken:
        return True, 'Authorization disabled'

    # Database connection is necessary to perform the authorization
    fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
    db_state=fgapisrv_db.getState()
    if db_state[0] != 0:
        return False, db_state[1]

    message = ''
    user_id = current_user.getId()
    user_name = current_user.getName()
    authZ = True

    # Check if requested action is in the user group roles
    authZ = authZ and fgapisrv_db.verifyUserRole(user_id,reqrole)
    if not authZ:
        message="User '%s' does not have '%s' role\n" % (user_name,reqrole)
    # Check current_user and filter user are different
    if user_name != user:
        user_impersonate  = fgapisrv_db.verifyUserRole(user_id,'user_impersonate')
        if user != "@":
            group_impersonate = fgapisrv_db.sameGroup(user_name,user) and fgapisrv_db.verifyUserRole(user_id,'group_impersonate')
        else:
            group_impersonate = fgapisrv_db.verifyUserRole(user_id,'group_impersonate')
        authZ = authZ and (user_impersonate or group_impersonate)
        if not authZ:
            if user == "*":
                user_text = "any user"
            elif user == "@":
                user_text = "group-wide users"
            else:
                user_text = "'%s' user" % user
            message="User '%s' cannot impersonate %s\n" % (user_name,user_text)
    # Check if app belongs to Group apps
    if(app_id is not None):
        authZ = authZ and fgapisrv_db.verifyUserApp(user_id,app_id)
        if not authZ:
            message="User '%s' cannot perform any activity on application having id: '%s'\n" % (usern_name,app_id)

    return authZ,message


##
## Routes as specified for APIServer at http://docs.csgfapis.apiary.io
##

#
# / path; used retrieve informative or service healty information
#
@app.route('/')
@app.route('/%s/' % fgapiver)
def index():
    versions = ({"id"    : fgapiver
                ,"_links": ({"rel" : "self"
                            ,"href": fgapiver },)
                ,"media-types": ({"type":"application/json"})
                ,"status": "prototype"
                ,'updated': "2016-04-20"
                ,"build:": __version__
                },)
    index_response = {
        "versions" : versions
       ,"_links"   : ({ "rel":"self"
                       ,"href": "/"},)
    }
    js = json.dumps(index_response,indent=fgjson_indent)
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp

##
## flask-login
##

# Retrieve the session token from Header Authorization field or from token in the argument list
# This function verifies the session token and return the user object if the check is successful
# The User object holds database user id and the associated user name
@login_manager.request_loader
def load_user(request):
    # Login manager could be disabled in conf file
    if fgapisrv_notoken:
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            user_id   = 0
            user_name = 'Unknown'
        else:
            user_info = fgapisrv_db.getUserInfoByName(fgapisrv_notokenusr)
            user_id   = user_info["id"]
            user_name = user_info["name"]
        print "Session token disabled; behaving has user: '%s' (%s)" % (user_name,user_id)
        return User(int(user_info["id"]),user_info["name"])

    token = request.headers.get('Authorization')
    if token is None:
        token = request.args.get('token')

    print "login_manager - token: '%s'" % token

    if token is not None:
        user_rec = verifySessionToken(token)
        print "login_manager - user_rec(0): '%s',user_rec(1): '%s'" % (user_rec[0],user_rec[1])
        if user_rec is not None and user_rec[0] is not None:
            return  User(user_rec[0],user_rec[1])
    return None


##
## Auth handlers
##

#
# /auth; used to provide a logtoken or username/password credentials and receive back an access token
#
@app.route('/auth',methods=['GET','POST'])
@app.route('/%s/auth' % fgapiver,methods=['GET','POST'])
def auth():
    token    = ""
    message  = ""
    logtoken = request.values.get('token')
    username = request.values.get('username')
    password = request.values.get('password')
    if request.method == 'GET':
        if logtoken is not None or len(token) > 0:
            # Retrieve access token from an login token
            token = createSessionToken(logtoken=logtoken)
        elif    username is not None and len(username) > 0\
            and password is not None and len(password) > 0:
            # Retrieve token from given username and password
            token = createSessionToken(username=username,password=password)
        else:
            message = "No credentials found!"
    elif request.method == 'POST':
        auth = request.headers.get('Authorization')
        auth_bearer = auth.split(" ") # Authorization: Bearer <Token>
        auth_creds0 = auth.split("/") # Authorization: <Username>/Base64(Password)
        auth_creds1 = auth.split(":") # Authorization: <Username>:Base64(Password)
        if len(auth_bearer) > 1 and auth_bearer[0] == "Bearer":
            # Retrieve access token from an login token
            token = createSessionToken(logtoken=auth_bearer[1])
        elif len(auth_creds0) > 1 and len(auth_creds0[0]) > 0 and len(auth_creds0[1]) > 0:
            # Retrieve token from given username and password
            token = createSessionToken(username=auth_creds0[0],password=base64.b64decode(auth_creds0[1]))
        elif len(auth_creds1) > 1 and len(auth_creds0[1]) > 0 and len(auth_creds1[1]) > 0:
            # Retrieve token from given username and password
            token = createSessionToken(username=auth_creds1[0],password=base64.b64decode(auth_creds1[1]))
        else:
            # No credentials found
            message = "No credentials found!"
    else:
        message = "Unhandled method: '%s'" % request.method
    if len(token)>0:
        response =  {
            "token": token
        }
        log_status = 200
    else:
        response = {
            "message": message
        }
        log_status = 404
    # include _links part
    response["_links"] = [{ "rel":"self"
                           ,"href": "/auth"},]
    js = json.dumps(response,indent=fgjson_indent)
    resp = Response(js, status=log_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp

##
## Task handlers
##

# tasks - used to view o create a new task
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution
@app.route('/%s/tasks' % fgapiver,methods=['GET','POST'])
@login_required
def tasks():
    user_name = current_user.getName()
    user_id   = current_user.getId()
    page      = request.values.get('page')
    per_page  = request.values.get('per_page')
    status    = request.values.get('status')
    user      = request.values.get('user',user_name)
    app_id    = request.values.get('application')
    task_state = 0

    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"task_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # Show the whole task list
            # Connect database
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_state = 404
                task_response = {
                    "message" : db_state[1]
                }
            else:
                # Before call user list check if * means ALL users or group restricted users (@)
                user_impersonate  = fgapisrv_db.verifyUserRole(user_id,'user_impersonate')
                group_impersonate = fgapisrv_db.sameGroup(user_name,user) and fgapisrv_db.verifyUserRole(user_id,'group_impersonate')
                if user == "*" and user_impersonate == False and group_impersonate == True:
                    user = "@" # Restrict tasks only to group members
                # Add the usernname info in case of * or @ filters
                if user == "*" or user == "@":
                    user=user+user_name
                # call to get tasks list
                task_list = fgapisrv_db.getTaskList(user,app_id)
                db_state=fgapisrv_db.getState()
                if db_state[0] != 0:
                    # DBError getting TaskList
                    # Prepare for 402
                    task_state = 402
                    task_response = {
                        "message" : db_state[1]
                    }
                else:
                    # Prepare response
                    task_response = {}
                    task_array = []
                    task_state = 200
                    for task_id in task_list:
                        task_record = fgapisrv_db.getTaskRecord(task_id)
                        db_state=fgapisrv_db.getState()
                        if db_state[0] != 0:
                            # DBError getting TaskRecord
                            # Prepare for 403
                            task_state = 403
                            task_array = {
                                "message" : db_state[1]
                            }
                        else:
                            task_array += [{
                                 "id"          : task_record['id']
                                ,"application" : task_record['application']
                                ,"description" : task_record['description']
                                ,"arguments"   : task_record['arguments']
                                ,"input_files" : task_record['input_files']
                                ,"output_files": task_record['output_files']
                                ,"status"      : task_record['status']
                                ,"user"        : task_record['user']
                                ,"date"        : str(task_record['creation'])
                                ,"last_change"        : str(task_record['last_change'])
                                ,"_links"      : [{
                                                     "rel" : "self"
                                                    ,"href": "/%s/tasks/%s" % (fgapiver,task_id)
                                                  }
                                                 ,{
                                                     "rel" : "input"
                                                    ,"href": "/%s/tasks/%s/input" % (fgapiver,task_id)
                                                  }]
                            },]
                    task_response = { "tasks" : task_array }
        # When page, per_page are not none (page=0..(len(task_response)/per_page)-1)
        # if page is not None and per_page is not None:
        # task_response = task_response[page*per_page:(page+1)*per_page]
        js = json.dumps(paginate_response(task_response,page,per_page),indent=fgjson_indent)
        resp = Response(js, status=task_state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        print "username %s - %s" % (user_name,user)
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_run")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # Getting values
            params = request.get_json()
            if params is not None:
                app_id   = params.get('application','')
                app_desc = params.get('description','')
                app_args = params.get('arguments'  ,[])
                app_inpf = params.get('input_files',[])
                app_outf = params.get('output_files',[])
                # Connect database
                fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                            ,db_port=fgapisrv_db_port
                                            ,db_user=fgapisrv_db_user
                                            ,db_pass=fgapisrv_db_pass
                                            ,db_name=fgapisrv_db_name
                                            ,iosandbbox_dir=fgapisrv_iosandbox
                                            ,geapiserverappid=fgapisrv_geappid)
                db_state=fgapisrv_db.getState()
                if db_state[0] != 0:
                    # Couldn't contact database
                    # Prepare for 404 not found
                    task_state = 404
                    task_response = {
                        "message" : db_state[1]
                    }
                else:
                    # Create task
                    task_id = fgapisrv_db.initTask(app_id
                                                  ,app_desc
                                                  ,user
                                                  ,app_args
                                                  ,app_inpf
                                                  ,app_outf)
                    if task_id < 0:
                        task_state = fgapisrv_db.getState()
                        # Error initializing task
                        # Prepare for 410 error
                        task_state = 410
                        task_response = {
                            'message' : task_state[1]
                        }
                    else:
                        # Prepare response
                        task_state = 200
                        task_record = fgapisrv_db.getTaskRecord(task_id)
                        task_response = {
                             "id"          : task_record['id']
                            ,"application" : task_record['application']
                            ,"description" : task_record['description']
                            ,"arguments"   : task_record['arguments']
                            ,"input_files" : task_record['input_files']
                            ,"output_files": task_record['output_files']
                            ,"status"      : task_record['status']
                            ,"user"        : task_record['user']
                            ,"date"        : str(task_record['last_change'])
                            ,"_links"      : [{
                                                 "rel" : "self"
                                                ,"href": "/%s/tasks/%s" % (fgapiver,task_id)
                                              }
                                             ,{
                                                 "rel" : "input"
                                                ,"href": "/%s/tasks/%s/input" % (fgapiver,task_id)
                                              }]
                        }
            else:
                task_state = 404
                task_response = {
                    "message" : "Did not find any application description json input"
                }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        if task_state == 200:
            resp.headers.add('Location','/v1.0/tasks/%s' % task_id)
            resp.headers.add('Link'
                            ,'</v1.0/tasks/%s/input>; rel="input", </v1.0/tasks/%s>; rel="self"'
                            %(task_id,task_id))
        return resp

# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)
@app.route('/%s/tasks/<task_id>' % fgapiver,methods=['GET','POST','DELETE','PATCH'])
@login_required
def task_id(task_id=None):
    user_name = current_user.getName()
    user_id   = current_user.getId()
    app_id    = getTaskAppId(task_id)
    user      = request.values.get('user',user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"task_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.taskExists(task_id):
                task_status = 404
                task_response = {
                    "message" : "Unable to find task with id: %s" % task_id
                }
            else:
                # Get task details
                task_response=fgapisrv_db.getTaskRecord(task_id)
                db_state=fgapisrv_db.getState()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    task_status = 404
                    task_response = {
                        "message" : db_state[1]
                    }
                else:
                    task_status = 200
        # Display task details
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"task_delete")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.taskExists(task_id):
                task_status = 404
                task_response = {
                    "message" : "Unable to find task with id: %s" % task_id
                }
            elif not fgapisrv_db.delete(task_id):
                task_status = 410
                task_response = {
                    "message" : "Unable to delete task with id: %s" % task_id
                }
            else:
                task_status = 200
                task_response = {
                    "message" : "Successfully removed task with id: %s" % task_id
                }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'PATCH':
        # PATCH on tasks accepts only changes on runtime_data
        # The input consists in a json having the form
        # { "runtime_data" : [ { "data_name":  "name"
        #                       ,"data_value": "value"
        #                       ,"data_desc": "description of the value"
        #                      }, ... ]
        # The insertion policy will be:
        #  1) data_name does not exists, a new record will be created in runtime_data table
        #  2) data_name exists the new value will be updated to the existing
        #
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"task_userdata")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            params = request.get_json()
            runtime_data = params.get('runtime_data',[])
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.taskExists(task_id):
                task_status = 404
                task_response = {
                    "message" : "Unable to find task with id: %s" % task_id
                }
            elif not fgapisrv_db.patch_task(task_id,runtime_data):
                task_status = 410
                task_response = {
                    "message" : "Unable to delete task with id: %s" % task_id
                }
            else:
                task_status = 200
                task_response = {
                    "message" : "Successfully patched task with id: %s" % task_id
                }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        task_response = {
            "message" : "Not supported method"
        }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=404, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp

# This finalizes the task request allowing to submit the task
# GET  - shows input files
# POST - specify input files
@app.route('/%s/tasks/<task_id>/input' % fgapiver,methods=['GET','POST'])
@login_required
def task_id_input(task_id=None):
    user_name = current_user.getName()
    user_id   = current_user.getId()
    app_id    = getTaskAppId(task_id)
    user      = request.values.get('user',user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"task_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # Display task_input_file details
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,geapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.taskExists(task_id):
                task_status = 404
                task_response = {
                    "message" : "Unable to find task with id: %s" % task_id
                }
            else:
                task_status = 204
                task_response = fgapisrv_db.getTaskRecord(task_id)['input_files']
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_run")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # First determine IO Sandbox location for this task
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.taskExists(task_id):
                task_status = 404
                task_response = {
                    "message" : "Unable to find task with id: %s" % task_id
                }
            else:
                task_sandbox = fgapisrv_db.getTaskIOSandbox(task_id)
                if task_sandbox is None:
                    task_status = 404
                    task_response = {
                        "message" : 'Could not find IO Sandbox dir for task: %s' % task_id
                    }
                else:
                    # Now process files to upload
                    uploaded_files = request.files.getlist('file[]')
                    file_list = ()
                    for f in uploaded_files:
                        filename = secure_filename(f.filename)
                        f.save(os.path.join(task_sandbox, filename))
                        fgapisrv_db.updateInputSandboxFile(task_id
                                                          ,filename
                                                          ,os.path.join(task_sandbox))
                        file_list+=(filename,)
                    # Now get input_sandbox status
                    if fgapisrv_db.isInputSandboxReady(task_id):
                        # The input_sandbox is completed; trigger the GE for this task
                        if fgapisrv_db.submitTask(task_id):
                            task_status = 200
                            task_response = {
                                 "task"    : task_id
                                ,"files"   : file_list
                                ,"message" : "uploaded"
                                ,"gestatus": "triggered"
                            }
                        else:
                            task_status = 412
                            task_response = {
                                "message" : fgapisrv_db.getState()[1]
                            }
                    else:
                        task_status = 200
                        task_response = {
                             "task"    : task_id
                            ,"files"   : file_list
                            ,"message" : "uploaded"
                            ,"gestatus": "waiting"
                        }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp

@app.route('/%s/file' % fgapiver,methods=['GET',])
@login_required
def file():
    serve_file = None
    user_name  = current_user.getName()
    user_id    = current_user.getId()
    user       = request.values.get('user',user_name)
    file_path  = request.values.get('path',None)
    file_name  = request.values.get('name',None)
    task_id    = getFileTaskId(file_name,file_path)
    app_id     = getTaskAppId(task_id)
    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_run")
        if not auth_state:
            task_state = 402
            file_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            try:
                serve_file = open('%s/%s' % (file_path,file_name),'rb')
                serve_file_content = serve_file.read()
                resp = Response(serve_file_content, status=200)
                resp.headers['Content-type'] = 'application/octet-stream'
                resp.headers.add('Content-Disposition','attachment; filename="%s"' % file_name)
                return resp
            except:
                file_response = {
                    "message" : "Unable to get file: %s/%s" % (file_path,file_name)
                }
            finally:
                if serve_file is not None:
                    serve_file.close()
        js = json.dumps(file_response,indent=fgjson_indent)
        resp = Response(js, status=404)
        resp.headers['Content-type'] = 'application/json'
        return resp

#
# APPLICATION
#

# application - used to view o create a new application
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution
@app.route('/%s/applications' % fgapiver,methods=['GET','POST'])
@login_required
def applications():
    user_name  = current_user.getName()
    user_id    = current_user.getId()
    app_id     = None
    user       = request.values.get('user',user_name)
    page     = request.values.get('page')
    per_page = request.values.get('per_page')
    user     = request.values.get('user')
    state = 0
    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # Show the whole task list
            # Connect database
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                state = 404
                response = {
                    "message" : db_state[1]
                }
            else:
                # call to get tasks
                app_list = fgapisrv_db.getAppList()
                db_state=fgapisrv_db.getState()
                if db_state[0] != 0:
                    # DBError getting TaskList
                    # Prepare for 402
                    state = 402
                    response = {
                        "message" : db_state[1]
                    }
                else:
                    # Prepare response
                    response = []
                    applications = []
                    state = 200
                    for app_id in app_list:
                        app_record = fgapisrv_db.getAppRecord(app_id)
                        db_state=fgapisrv_db.getState()
                        if db_state[0] != 0:
                            # DBError getting TaskRecord
                            # Prepare for 403
                            state = 403
                            response = {
                                "message" : db_state[1]
                            }
                        else:
                            applications += [{
                                 "id"             : app_record['id']
                                ,"name"           : app_record['name']
                                ,"description"    : app_record['description']
                                ,"outcome"        : app_record['outcome']
                                ,"enabled"        : app_record['enabled']
                                ,"parameters"     : app_record['parameters']
                                ,"input_files"    : app_record['input_files']
                                ,"infrastructures": app_record['infrastructures']
                                ,"_links"         : [{
                                                       "rel" : "self"
                                                      ,"href": "/%s/application/%s" % (fgapiver,app_id)
                                                     }]
                            },]
                    response = { "applications": applications }
        # When page, per_page are not none (page=0..(len(task_response)/per_page)-1)
        # if page is not None and per_page is not None:
        # task_response = task_response[page*per_page:(page+1)*per_page]
        js = json.dumps(paginate_response(response,page,per_page),indent=fgjson_indent)
        resp = Response(js, status=state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_install")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            # Getting values
            params          = request.get_json()
            name            = params.get('name','')
            description     = params.get('description','')
            outcome         = params.get('outcome','JOB')
            enabled         = params.get('enabled'  ,[])
            parameters      = params.get('parameters',[])
            inp_files       = params.get('input_files',[])
            infrastructures = params.get('infrastructures',[])
            # Connect database
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,geapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                state = 404
                response = {
                    "message" : db_state[1]
                }
            else:
                # Create app
                app_id = fgapisrv_db.initApp(name
                                            ,description
                                            ,outcome
                                            ,enabled
                                            ,parameters
                                            ,inp_files
                                            ,infrastructures
                                            )
                if app_id < 0:
                    state = fgapisrv_db.getState()
                    # Error initializing task
                    # Prepare for 410 error
                    state = 410
                    response = {
                        "message" : task_state[1]
                    }
                else:
                    # Prepare response
                    state = 200
                    app_record = fgapisrv_db.getAppRecord(app_id)
                    response = {
                                 "id"             : app_record['id']
                                ,"name"           : app_record['name']
                                ,"description"    : app_record['description']
                                ,"enabled"        : app_record['enabled']
                                ,"parameters"     : app_record['parameters']
                                ,"input_files"    : app_record['input_files']
                                ,"infrastructures": app_record['infrastructures']
                                ,"_links"         : [{
                                                       "rel" : "self"
                                                      ,"href": "/%s/application/%s" % (fgapiver,app_id)
                                                     }]
                               }
        js = json.dumps(response,indent=fgjson_indent)
        resp = Response(js, status=state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        if state == 200:
            resp.headers.add('Location','/v1.0/tasks/%s' % task_id)
            resp.headers.add('Link'
                            ,'</v1.0/tasks/%s/input>; rel="input", </v1.0/tasks/%s>; rel="self"'
                            %(task_id,task_id))
        return resp

# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)
@app.route('/%s/applications/<app_id>' % fgapiver,methods=['GET', 'DELETE', 'POST'])
@login_required
def app_id(app_id=None):
    user_name  = current_user.getName()
    user_id    = current_user.getId()
    user       = request.values.get('user',user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                status = 404
                response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.appExists(app_id):
                status = 404
                response = {
                    "message" : "Unable to find application with id: %s" % app_id
                }
            else:
                # Get task details
                response=fgapisrv_db.getAppRecord(app_id)
                db_state=fgapisrv_db.getState()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    status = 404
                    response = {
                        "message" : db_state[1]
                    }
                else:
                    status = 200
        # Display task details
        js = json.dumps(response,indent=fgjson_indent)
        resp = Response(js, status=status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorizeUser(current_user,app_id,user,"app_delete")
        if not auth_state:
            task_state = 402
            task_response = {
                "message" : "Not authorized to perform this request:\n%s" % auth_msg
            }
        else:
            fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                        ,db_port=fgapisrv_db_port
                                        ,db_user=fgapisrv_db_user
                                        ,db_pass=fgapisrv_db_pass
                                        ,db_name=fgapisrv_db_name
                                        ,iosandbbox_dir=fgapisrv_iosandbox
                                        ,fgapiserverappid=fgapisrv_geappid)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't contact database
                # Prepare for 404 not found
                status = 404
                response = {
                    "message" : db_state[1]
                }
            elif not fgapisrv_db.appExists(app_id):
                status = 404
                response = {
                    "message" : "Unable to find application with id: %s" % app_id
                }
            elif not fgapisrv_db.appDelete(app_id):
                status = 410
                response = {
                    "message" : "Unable to delete application with id: %s" % app_id
                }
            else:
                status = 200
                response = {
                    "message" : "Successfully removed application with id: %s" % app_id
                }
        js = json.dumps(response,indent=fgjson_indent)
        resp = Response(js, status=status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        task_response = {
            "message" : "Not supported method"
        }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=404, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp

# Common header section
@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH')
  response.headers.add('Access-Control-Allow-Credentials', 'true')
  response.headers.add('Server',fgapiserver_name)
  return response

#
# The app starts here
#

# First check the db
checkDbVer()

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    if len(fgapisrv_crt) > 0 and len(fgapisrv_key) > 0:
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(fgapisrv_key)
        context.use_certificate_file(fgapisrv_crt)
        app.run(host=fgapisrv_host, port=fgapisrv_port, ssl_context=context, debug=fgapisrv_debug)
    else:
        app.run(host=fgapisrv_host, port=fgapisrv_port,debug=fgapisrv_debug)
