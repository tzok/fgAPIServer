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
__version__    = "1.0"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

"""
  GridEngine API Server database
"""
import MySQLdb
import uuid
import os
import random
import urllib

"""
 Task sandboxing will be placed here
 Sandbox directories will be generated as UUID names generated during task creation
"""
iosandbbox_dir   = '/tmp'
geapiserverappid = '10000' # GridEngine sees API server as an application
"""
 Database connection default settings
"""
db_host = 'localhost'
db_port = 3306
db_user = 'geapiserver'
db_pass = 'geapiserver_password'
db_name = 'geapiserver'

"""
  geapiserver_db Class contain any call interacting with geapiserver database
"""
class geapiserver_db:

    db_host = None
    db_port = None
    db_user = None
    db_pass = None
    db_name = None

    err_flag = False
    err_msg  = ''
    message  = ''

    """
      geapiserver_db - Constructor may override default values defined at the top of the file
    """
    def __init__(self,*args, **kwargs):
        self.db_host = kwargs.get('db_host',db_host)
        self.db_port = kwargs.get('db_port',db_port)
        self.db_user = kwargs.get('db_user',db_user)
        self.db_pass = kwargs.get('db_pass',db_pass)
        self.db_name = kwargs.get('db_name',db_name)

    """
      connect Connects to the geapiserver database
    """
    def connect(self):
        return MySQLdb.connect(host=self.db_host
                              ,user=self.db_user
                              ,passwd=self.db_pass
                              ,db=self.db_name
                              ,port=self.db_port)

    def test(self):
        db     = None
        cursor = None
        try:
            db = self.connect()
            # prepare a cursor object using cursor() method
            cursor = db.cursor()
            # execute SQL query using execute() method.
            cursor.execute("SELECT VERSION()")
            # Fetch a single row using fetchone() method.
            data = cursor.fetchone()
            self.err_flag = False
            self.err_msg  = 'Database version : %s' % data[0]
        except MySQLdb.Error, e:
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()


    """
      getState returns the status and message of the last action on the DB
    """
    def getState(self):
        return (self.err_flag,self.err_msg)

    """
      taskExists - Return True if the given task_id exists False otherwise
    """
    def taskExists(self,task_id):
        db     = None
        cursor = None
        count = 0
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select count(*)\n'
                 'from task\n'
                 'where id = %s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            count = cursor.fetchone()[0]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()
        return count > 0

    """
       getTaskRecord
    """
    def getTaskRecord(self,task_id):
        db     = None
        cursor = None
        task_record = {}
        try:
            db=self.connect()
            cursor = db.cursor()
            # Task record
            sql=('select id\n'
                 '      ,status\n'
                 '      ,creation\n'
                 '      ,last_change\n'
                 '      ,app_id\n'
                 '      ,description\n'
                 '      ,status\n'
                 '      ,user\n'
                 '      ,iosandbox\n'
                 'from task where id=%s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_dbrec=cursor.fetchone()
            if task_dbrec is not None:
                task_dicrec={ 'id'          : task_dbrec[0]
                             ,'status'      : task_dbrec[1]
                             ,'creation'    : task_dbrec[2]
                             ,'last_change' : task_dbrec[3]
                             ,'app_id'      : task_dbrec[4]
                             ,'description' : task_dbrec[5]
                             ,'status'      : task_dbrec[6]
                             ,'user'        : task_dbrec[7]
                             ,'iosandbox'   : task_dbrec[8]
                            }
            else:
                return {}
            # Task arguments
            sql=('select argument\n'
                 'from task_arguments\n'
                 'where task_id=%s\n'
                 'order by arg_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_args=()
            for arg in cursor:
                task_args+=(arg[0],)
            # Task input files
            sql=('select file\n'
                 'from task_input_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ifiles=()
            for ifile in cursor:
                task_ifiles+=(ifile[0],)
            # Task output files
            sql=('select file\n'
                 '      ,if(path is NULL,\'\',path)\n'
                 'from task_output_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ofiles=()
            for ofile in cursor:
                ofile_entry = {
                    'name' : ofile[0]
                   ,'url'  : 'file?%s' % urllib.urlencode({'path':ofile[1]
                                                          ,'name':ofile[0]})
                }
                task_ofiles+=(ofile_entry,)
            # Prepare output
            task_record= {
                 'id'          : task_dicrec['id']
                ,'status'      : task_dicrec['status']
                ,'creation'    : str(task_dicrec['creation'])
                ,'last_change' : str(task_dicrec['last_change'])
                ,'app_id'      : task_dicrec['app_id']
                ,'description' : task_dicrec['description']
                ,'user'        : task_dicrec['user']
                ,'arguments'   : task_args
                ,'input_files' : task_ifiles
                ,'output_files': task_ofiles
                ,'iosandbox'   : task_dicrec['iosandbox']
            }
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:
                db.commit()
                db.close()
        return task_record

    """
      getTaskState - Return the status of a given Task
    """
    def getTaskStatus(self,task_id):
        return self.getTaskRecord(task_id).get('status',None)

    """
      getTaskInputFiles - Return information about InputFiles of a given Task
    """
    def getTaskInputFiles(self,task_id):
        db     = None
        cursor = None
        task_ifiles=()
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select file\n'
                 '      ,if(path is null,\'waiting\',\'ready\')\n'
                 'from task_input_file\n'
                 'where task_id = %s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            for ifile in cursor:
                file_info = {
                    'name'  : ifile[0]
                   ,'status': ifile[1]
                }
                task_ifiles+=(file_info,)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()
        return task_ifiles

    """
      getTaskOutputFiles - Return information about OutputFiles of a given Task
    """
    def getTaskOutputFiles(self,task_id):
        db     = None
        cursor = None
        task_ifiles=()
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select file\n'
                 '      ,if(path is null,\'waiting\',\'ready\')\n'
                 'from task_output_file\n'
                 'where task_id = %s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            for ifile in cursor:
                file_info = {
                    'name'  : ifile[0]
                   ,'status': ifile[1]
                }
                task_ifiles+=(file_info,)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()
        return task_ifiles

    """
      getAppDetail - Return details about a given app_id
    """
    def getAppDetail(self,app_id):
        db     = None
        cursor = None
        app_detail = {}
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select id\n'
                 '      ,name\n'
                 '      ,description\n'
                 '      ,creation\n'
                 '      ,enabled\n'
                 'from application\n'
                 'where id=%s;')
            sql_data=(app_id,)
            cursor.execute(sql,sql_data)
            app_record=cursor.fetchone()
            app_detail = {
                'id'          : app_record[0]
               ,'name'        : app_record[1]
               ,'description' : app_record[2]
               ,'creation'    : str(app_record[3])
               ,'enabled'     : app_record[4]
            }
            # Add now app parameters
            sql=('select pname\n'
                 '      ,pvalue\n'
                 'from application_parameter\n'
                 'where app_id=%s\n'
                 'order by param_id asc;')
            sql_data=(app_id,)
            cursor.execute(sql,sql_data)
            app_parameters=()
            for param in cursor:
                parameter = {
                     'param_name' : param[0]
                    ,'param_value': param[1]
                }
                app_parameters+=(parameter,)
            app_detail['parameters']=app_parameters
            # Get now application ifnrastructures with their params
            infrastructures=()
            sql=('select id\n'
                 '      ,name\n'
                 '      ,description\n'
                 '      ,creation\n'
                 '      ,if(enabled,\'enabled\',\'disabled\') status\n'
                 'from infrastructure\n'
                 'where app_id=%s;')
            sql_data=(app_id,)
            cursor.execute(sql,sql_data)
            infrastructures = ()
            for infra in cursor:
                infra_details = {
                     'id'         : infra[0]
                    ,'name'       : infra[1]
                    ,'description': infra[2]
                    ,'creation'   : str(infra[3])
                    ,'status'     : infra[4]
                }
                infrastructures+=(infra_details,)
            # Now loop over infrastructures to get their parameters
            for infra in infrastructures:
                sql=('select pname, pvalue\n'
                     'from infrastructure_parameter\n'
                     'where infra_id=%s\n'
                     'order by param_id asc;')
                sql_data=(str(infra['id']),)
                cursor.execute(sql,sql_data)
                infra_parameters = ()
                for param in cursor:
                    param_details = {
                         'name' : param[0]
                        ,'value': param[1]
                    }
                    infra_parameters+=(param_details,)
                infra['parameters']=infra_parameters
            app_detail['infrastructures']=infrastructures
            return app_detail
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()

    """
      getTaskAppDetail - Return application details of a given Task
    """
    def getTaskAppDetail(self,task_id):
        task_record = self.getTaskRecord(task_id)
        return self.getAppDetail(str(task_record['app_id']))

    """
      getTaskInfo - Retrieve full information about given task_id
    """
    def getTaskInfo(self,task_id):
        task_record = self.getTaskRecord(task_id)
        task_record.get('id',None)
        if task_record.get('id',None) is None:
            self.err_flag=True
            self.err_msg="[ERROR] Did not find task id: %s" % task_id
            return {}
        task_app_details = self.getTaskAppDetail(task_id)
        task_info = task_record
        del task_info['app_id']
        task_info['application']=task_app_details
        return task_info

    """
      initTask initialize a task from a given application id
    """
    def initTask(self,app_id,description,user,arguments,input_files,output_files):
        db     = None
        cursor = None
        task_id=-1
        # Create the Task IO Sandbox
        try:
            iosandbox = '%s/%s' % (iosandbbox_dir,str(uuid.uuid1()))
            os.makedirs(iosandbox)
            # Insert new Task
            db=self.connect()
            cursor = db.cursor()
            sql=('insert into task (id\n'
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
                 'from task;\n'
                )
            sql_data = (app_id,description,user,iosandbox)
            cursor.execute(sql,sql_data)
            sql='select max(id) from task;'
            sql_data=''
            cursor.execute(sql)
            task_id = cursor.fetchone()[0]
            # Insert Task arguments
            if arguments != []:
                for arg in arguments:
                    sql=('insert into task_arguments (task_id\n'
                         '                           ,arg_id\n'
                         '                           ,argument)\n'
                         'select %s                                          -- task_id\n'
                         '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)     -- arg_id\n'
                         '      ,%s                                          -- argument\n'
                         'from task_arguments\n'
                         'where task_id=%s'
                        )
                    sql_data=(task_id,arg,task_id)
                    cursor.execute(sql,sql_data)
            # Insert Task input_files
            if input_files != []:
                for inpfile in input_files:
                    sql=('insert into task_input_file (task_id\n'
                         '                            ,file_id\n'
                         '                            ,file)\n'
                         'select %s                                          -- task_id\n'
                         '      ,if(max(file_id) is NULL,1,max(file_id)+1)   -- file_id\n'
                         '      ,%s                                          -- file\n'
                         'from task_input_file\n'
                         'where task_id=%s'
                        )
                    sql_data=(task_id,inpfile,task_id)
                    cursor.execute(sql,sql_data)
            # Insert Task output_files specified by application settings (default)
            sql=('select pvalue\n'
                 'from application_parameter\n'
                 'where app_id=%s\n'
                 ' and pname=\'jobdesc_output\'\n'
                 '  or pname=\'jobdesc_error\';')
            sql_data=(app_id,)
            cursor.execute(sql,sql_data)
            for out_file in cursor:
                output_files+=[out_file[0],]
            # Insert Task output_files specified by user
            for outfile in output_files:
                sql=('insert into task_output_file (task_id\n'
                     '                             ,file_id\n'
                     '                             ,file)\n'
                     'select %s                                          -- task_id\n'
                     '      ,if(max(file_id) is NULL,1,max(file_id)+1)   -- file_id\n'
                     '      ,%s                                          -- file\n'
                     'from task_output_file\n'
                     'where task_id=%s'
                    )
                sql_data=(task_id,outfile,task_id)
                cursor.execute(sql,sql_data)
        except IOError as (errno, strerror):
            self.err_flag = True
            self.err_msg  =  "I/O error({0}): {1}".format(errno, strerror)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:
                db.commit()
                db.close()
        return task_id

    """
      getTaskIOSandbox - Get the assigned IO Sandbox folder of the given task_id
    """
    def getTaskIOSandbox(self,task_id):
        db     = None
        cursor = None
        iosandbox = None
        try:
            db=self.connect()
            cursor = db.cursor()
            sql='select iosandbox from task where id=%s;'
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            result = cursor.fetchone()
            if result is None:
                self.err_flag = True
                self.err_msg  = "[ERROR] Unable to find task id: %s" % task_id
            else:
                iosandbox = result[0]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()
        return iosandbox

    """
      updateInputSandboxFile - Update input_sandbox_table with the fullpath of a given (task,filename)
    """
    def updateInputSandboxFile(self,task_id,filename,filepath):
        db     = None
        cursor = None
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('update task_input_file\n'
                 'set path=%s\n'
                 'where task_id=%s\n'
                 '  and file=%s;')
            sql_data=(filepath,task_id,filename)
            cursor.execute(sql,sql_data)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:
                db.commit()
                db.close()
        return

    """
      isInputSandboxReady - Return true if all input_sandbox files have been uploaded for a given (task_id)
                            True if all files have a file path registered or the task does not contain any
                            input file
    """
    def isInputSandboxReady(self,task_id):
        db     = None
        cursor = None
        sandbox_ready = False
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
                 'from task_input_file\n'
                 'where task_id=%s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            sandbox_ready = cursor.fetchone()[0]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None:     db.close()
        return 1==int(sandbox_ready)

    """
      submitTaks - Trigger the GridEngine to submit the given task
                   This function takes care of all GridEngine needs to properly submit the applciation
    """
    def submitTaks(self,task_id):
        # Get task information
        task_info = self.getTaskInfo(task_id)
        app_info=task_info['application']
        app_params=app_info['parameters']
        # Retrieve only enabled infrastructures
        app_infras=()
        for infra in app_info['infrastructures']:
            if bool(infra['status']):
                app_infras+=(infra,)
        if app_infras is None or len(app_infras) == 0:
            self.err_flag = True
            self.err_msg  = 'No suitable infrastructure found for task_id: %s' % task_id
            return False
        # Proceed only if task comes form a WAITING state
        task_status = task_info.get('status','')
        if task_status != 'WAITING':
            self.err_flag = True
            self.err_msg  = 'Wrong status (\'%s\') to ask submission for task_id: %s' % (task_status,task_id)
            return False
        # Application must be also enabled
        if not bool(app_info['enabled']):
            self.err_flag = True
            self.err_msg  = 'Unable submit task_id: %s, because application is disabled' % task_id
            return False
        # Prepare GridEngine required info (JSON file)
        """
        task_info contains:
        { "status": "WAITING"
        , "description": "helloworld@localhost test run"
        , "creation": "2015-10-08 16:22:51"
        , "user": "brunor"
        , "id": 1
        , "output_files": ["hello.out", "hello.err"]
        , "application": {"description": "hostname tester application"
                         , "parameters": [{"param_name": "jobdesc_executable", "param_value": "/bin/hostname"}
                                        , {"param_name": "jobdesc_arguments", "param_value": "-f"}
                                        , {"param_name": "jobdesc_output", "param_value": "stdout.txt"}
                                        , {"param_name": "jobdesc_error", "param_value": "stderr.txt"}]
                         , "creation": "2015-10-08 16:12:17"
                         , "enabled": 1
                         , "infrastructures": [ {"status": "enabled"
                                               , "description": "hostname application on localhost"
                                               , "parameters": [{"name": "jobservice", "value": "fork://localhost"}]
                                               , "creation": "2015-10-08 16:12:18"
                                               , "id": 1
                                               , "name": "hostname@localhost"}]
                        , "id": 1
                        , "name": "hostname"
                        }
        , "arguments": ["arg1", "arg2", "arg3"]
        , "input_files": ["hello.txt", "hello.sh"]
        , "last_change": "2015-10-08 16:22:51"}
        GridEngine understands:
        {
           "commonName": "helloworld@localhost test run",
           "application": 10000, -- Refers to the GridEngine APIServer registered app
           "identifier": "task_id: 1",
           "jobDescription": {
               "executable": "hostname",
               "output": "stdout.txt",
               "error": "stderr.txt"
               "arguments": "-f"
           },
           "infrastructure": {
               "resourceManagers": "fork://localhost"
           }
        }
        """
        GridEngineTaskDescription = {}
        GridEngineTaskDescription['commonName' ] = '%s' % task_info['user']
        GridEngineTaskDescription['application'] = '%s' % geapiserverappid
        GridEngineTaskDescription['identifier' ] = 'task_id: %s' % task_info['id']
        # Prepare the JobDescription
        GridEgnineJobDescription = {}
        for param in app_params:
            if param['param_name']=='jobdesc_executable':
                GridEgnineJobDescription['executable']=param['param_value']
            elif param['param_name']=='jobdesc_arguments':
                GridEgnineJobDescription['arguments']=param['param_value']+' '
            elif param['param_name']=='jobdesc_output':
                GridEgnineJobDescription['output']=param['param_value']
            elif param['param_name']=='jobdesc_error':
                GridEgnineJobDescription['error']=param['param_value']
            #else: - here a warning should arose
        # Now add further arguments if specified in task
        for arg in task_info.get('arguments',[]):
            GridEgnineJobDescription['arguments']+='%s ' % arg
        GridEgnineJobDescription['arguments']=GridEgnineJobDescription['arguments'].strip()
        # Get application specific settings
        GridEngineTaskDescription['jobDescription'] = GridEgnineJobDescription
        # Select one of the possible infrastructures defined for this application
        # A random strategy is currently implemented; this could be changed later
        if len(app_infras) > 1:
           sel_infra = app_infras[int(random.random()*(len(app_infras)+1))]
        else:
           sel_infra = app_infras[0]
        # Get resource manager
        GridEngineInfrastructure = {}
        GridEngineCredentials    = {}
        for param in sel_infra['parameters']:
            if param['name'] == 'jobservice':
                GridEngineInfrastructure['resourceManagers'] = param['value']
            elif param['name'] == 'username':
                GridEngineCredentials['username'] = param['value']
            elif param['name'] == 'password':
                GridEngineCredentials['password'] = param['value']
            #else: - here a warning should arose
        GridEngineTaskDescription['infrastructure'] = GridEngineInfrastructure
        GridEngineTaskDescription['credentials'] = GridEngineCredentials
        # Switch task status and populate gequeue table accordingly
        return self.enqueueGridEngine(task_info,GridEngineTaskDescription)

    def enqueueGridEngine(self,task_info,ge_desc):
        db      = None
        cursor  = None
        ge_file = None
        self.err_flag = False
        try:
            # Save first the GridEngine task description file, which has the format:
            # <task_iosandbox_dir>/<task_id>.info
            ge_file=open('%s/%s.info' % (task_info['iosandbox'],task_info['id']),"w")
            ge_file.write(str(ge_desc))
            try:
                # Insert task record in the GridEngine' queue
                db=self.connect()
                cursor = db.cursor()
                sql=('insert into ge_queue (\n'
                     '   task_id      -- Taks reference for this GridEngine queue entry\n'
                     '  ,agi_id       -- UsersTracking\' ActiveGridInteraction id reference\n'
                     '  ,action       -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...\n'
                     '  ,status       -- Operation status: QUEUED,PROCESSING,PROCESSED,FAILED,DONE\n'
                     '  ,ge_status    -- GridEngine Job Status: WAITING,SCHEDULED,RUNNING,ABORT,DONE\n'
                     '  ,creation     -- When the action is enqueued\n'
                     '  ,last_change  -- When the record has been modified by the GridEngine last time\n'
                     '  ,action_info  -- Temporary directory path containing further info to accomplish the requested operation\n'
                     ') values (%s,NULL,\'SUBMIT\',\'QUEUED\',NULL,now(),now(),%s);'
                    )
                sql_data=(task_info['id'],task_info['iosandbox'])
                cursor.execute(sql,sql_data)
                sql=('update task set status=\'SUBMIT\', last_change=now() where id=%s;'
                    )
                sql_data=(str(task_info['id']),)
                cursor.execute(sql,sql_data)
            except MySQLdb.Error, e:
                db.rollback()
                self.err_flag = True
                self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
            finally:
                if cursor  is not None: cursor.close()
                if     db  is not None:
                    db.commit()
                    db.close()
                if ge_file is not None: ge_file.close()
        except IOError as (errno, strerror):
            self.err_flag = True
            self.err_msg  = "I/O error({0}): {1}".format(errno, strerror)
        finally:
            ge_file.close()
        return not self.err_flag

    """
      delete - Delete a given task
    """
    def delete(self,task_id):
        status=False
        # Get task information
        task_info = self.getTaskInfo(task_id)
        try:
            # Insert task record in the GridEngine' queue
            db=self.connect()
            cursor = db.cursor()
            sql=('insert into ge_queue (\n'
                 '   task_id      -- Taks reference for this GridEngine queue entry\n'
                 '  ,agi_id       -- UsersTracking\' ActiveGridInteraction id reference\n'
                 '  ,action       -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...\n'
                 '  ,status       -- Operation status: QUEUED,PROCESSING,PROCESSED,FAILED,DONE\n'
                 '  ,ge_status    -- GridEngine Job Status: WAITING,SCHEDULED,RUNNING,ABORT,DONE\n'
                 '  ,creation     -- When the action is enqueued\n'
                 '  ,last_change  -- When the record has been modified by the GridEngine last time\n'
                 '  ,action_info  -- Temporary directory path containing further info to accomplish the requested operation\n'
                 ') values (%s,NULL,\'JOBCANCEL\',\'QUEUED\',NULL,now(),now(),%s);'
                )
            sql_data=(task_info['id'],task_info['iosandbox'])
            cursor.execute(sql,sql_data)
            sql=('update task set status=\'CANCELLED\', last_change=now() where id=%s;'
                )
            sql_data=(str(task_info['id']),)
            cursor.execute(sql,sql_data)
            status=True
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor  is not None: cursor.close()
            if     db  is not None:
                db.commit()
                db.close()
        return status
