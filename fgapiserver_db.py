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
import shutil

"""
 Database connection default settings
"""
def_db_host = 'localhost'
def_db_port = 3306
def_db_user = 'fgapiserver'
def_db_pass = 'fgapiserver_password'
def_db_name = 'fgapiserver'

"""
 Task sandboxing will be placed here
 Sandbox directories will be generated as UUID names generated during task creation
"""
def_iosandbbox_dir   = '/tmp'
def_geapiserverappid = '10000' # GridEngine sees API server as an application

"""
  fgapiserver_db Class contain any call interacting with fgapiserver database
"""
class fgapiserver_db:

    """
     API Server Database connection settings
    """
    db_host = None
    db_port = None
    db_user = None
    db_pass = None
    db_name = None
    iosandbbox_dir   = def_iosandbbox_dir
    geapiserverappid = def_geapiserverappid

    """
        Error Flag and messages filled up upon failures
    """
    err_flag = False
    err_msg  = ''
    message  = ''

    """
      geapiserver_db - Constructor may override default values defined at the top of the file
    """
    def __init__(self,*args, **kwargs):
        self.db_host          = kwargs.get('db_host',def_db_host)
        self.db_port          = kwargs.get('db_port',def_db_port)
        self.db_user          = kwargs.get('db_user',def_db_user)
        self.db_pass          = kwargs.get('db_pass',def_db_pass)
        self.db_name          = kwargs.get('db_name',def_db_name)
        self.iosandbbox_dir   = kwargs.get('iosandbbox_dir',def_iosandbbox_dir)
        self.geapiserverappid = kwargs.get('geapiserverappid',def_geapiserverappid)


    """
      connect Connects to the fgapiserver database
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
            task_args=[]
            for arg in cursor:
                task_args+=[arg[0],]
            # Task input files
            sql=('select file\n'
                 'from task_input_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ifiles=[]
            for ifile in cursor:
                task_ifiles+=[ifile[0],]
            # Task output files
            sql=('select file\n'
                 '      ,if(path is NULL,\'\',path)\n'
                 'from task_output_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ofiles=[]
            for ofile in cursor:
                ofile_entry = {
                    'name' : ofile[0]
                   ,'url'  : 'file?%s' % urllib.urlencode({'path':ofile[1]
                                                          ,'name':ofile[0]})
                }
                task_ofiles+=[ofile_entry,]
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
        Retrieve from application_files table the application specific files
        associated to the given application
    """
    def getAppFiles(self,app_id):
        db     = None
        cursor = None
        app_files=[]
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select file\n'
                 '      ,path\n'
                 '      ,override\n'
                 'from application_file\n'
                 'where app_id=%s\n'
                 'order by file_id asc;')
            sql_data=(app_id,)
            cursor.execute(sql,sql_data)
            for app_file in cursor:
                app_files+= [{
                     'file'    : app_file[0]
                    ,'path'    : app_file[1]
                    ,'override': app_file[2]
                },]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor is not None: cursor.close()
            if     db is not None: db.close()
        return app_files

    """
      initTask initialize a task from a given application id
    """
    def initTask(self,app_id,description,user,arguments,input_files,output_files):
        # Get app defined files
        app_files = self.getAppFiles(app_id)
        # Start creating task
        db     = None
        cursor = None
        task_id=-1
        try:
            # Create the Task IO Sandbox
            iosandbox = '%s/%s' % (self.iosandbbox_dir,str(uuid.uuid1()))
            os.makedirs(iosandbox)
            # Insert new Task record
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
            # Process input files specified in the REST URL (input_files)
            # producing a new vector called inp_file having the same structure
            # of app_files: [ { 'name': <filname>
            #                  ,'path': <path to file> },...]
            # except for the 'override' key not necessary in this second array.
            # For each file specified inside input_file, verify if it exists alredy
            # in the app_file vector. If the file exists there are two possibilities:
            # * app_file['override'] flag is true; then user inputs are ignored, thus
            # the file will be skipped
            # * app_file['override'] flag is false; user input couldn't ignored, thus
            # the path to the file will be set to NULL waiting for user input
            inp_file = []
            for file in input_files:
                print "file: '%s'" % file
                skip_file=False
                for app_file in app_files:
                    if file == app_file['file']:
                        skip_file = True
                        if app_file['override'] is True:
                            break
                        else:
                            app_file['path'] = None
                            break
                if not skip_file:
                    # The file is not in app_file
                    inp_file += [{ 'path': None
                                  ,'file': file },]
            # Files can be registered in task_input_files
            for inpfile in app_files+inp_file:
                # Not None paths refers to existing app_files that could be copied
                # into the iosandbox task directory; then use iosandbox path
                if inpfile['path'] is not None:
                    shutil.copy('%s/%s' % (inpfile['path'],inpfile['file'])
                               ,'%s/%s' % (iosandbox,inpfile['file']))
                    inpfile['path'] = iosandbox
                sql=('insert into task_input_file (task_id\n'
                     '                            ,file_id\n'
                     '                            ,path\n'
                     '                            ,file)\n'
                     'select %s                                          -- task_id\n'
                     '      ,if(max(file_id) is NULL,1,max(file_id)+1)   -- file_id\n'
                     '      ,%s                                          -- path\n'
                     '      ,%s                                          -- file\n'
                     'from task_input_file\n'
                     'where task_id=%s'
                    )
                sql_data=(task_id,inpfile['path'],inpfile['file'],task_id)
                cursor.execute(sql,sql_data)
            # Insert Task output_files specified by application settings (default)
            sql=('select pvalue\n'
                 'from application_parameter\n'
                 'where app_id=%s\n'
                 ' and (   pname=\'jobdesc_output\'\n'
                 '      or pname=\'jobdesc_error\');')
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
        # Infrastructures must exist for this application
        enabled_infras=[]
        for infra in app_infras:
            if infra['status'] == 'enabled':
                enabled_infras += [infra,]
        if len(enabled_infras) == 0:
            self.err_flag = True
            self.err_msg  = 'No suitable infrastructures found for task_id: %s' % task_id
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
        GridEngineTaskDescription['application'] = '%s' % self.geapiserverappid
        GridEngineTaskDescription['identifier' ] = '%s@%s' % (task_info['id'],task_info['iosandbox'])
        GridEngineTaskDescription['input_files'] = task_info['input_files']
        GridEngineTaskDescription['output_files'] = task_info['output_files']
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
        if len(enabled_infras) > 1:
            sel_infra = app_infras[int(random.random()*len(enabled_infras))]
        else:
            sel_infra = enabled_infras[0]
        # Get resource manager
        GridEngineInfrastructure = {}
        GridEngineCredentials    = {}
        for param in sel_infra['parameters']:
            if param['name'] == 'jobservice':
                GridEngineInfrastructure['resourceManagers'] = param['value']
            elif param['name'] == 'os_tpl':
                GridEngineInfrastructure['os_tpl'] = param['value']
            elif param['name'] == 'resource_tpl':
                GridEngineInfrastructure['resource_tpl'] = param['value']
            elif param['name'] == 'attributes_title':
                GridEngineInfrastructure['attributes_title'] = param['value']
            elif param['name'] == 'bdii':
                GridEngineInfrastructure['bdii']=param['value']
            elif param['name'] == 'swtags':
                GridEngineInfrastructure['swtags']=param['value']
            elif param['name'] == 'jdlRequirements':
                GridEngineInfrastructure['jdlRequirements']=param['value']
            elif param['name'] == 'username':
                GridEngineCredentials['username'] = param['value']
            elif param['name'] == 'password':
                GridEngineCredentials['password'] = param['value']
            elif param['name'] == 'eToken_host':
                GridEngineCredentials['eToken_host'] = param['value']
            elif param['name'] == 'eToken_port':
                GridEngineCredentials['eToken_port'] = param['value']
            elif param['name'] == 'eToken_id':
                GridEngineCredentials['eToken_id'] = param['value']
            elif param['name'] == 'voms':
                GridEngineCredentials['voms'] = param['value']
            elif param['name'] == 'voms_role':
                GridEngineCredentials['voms_role'] = param['value']
            elif param['name'] == 'rfc_proxy':
                GridEngineCredentials['rfc_proxy'] = param['value']
            #else: - here a warning should come
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
            # Now save native APIServer JSON file, having the format:
            # <task_iosandbox_dir>/<task_id>.json
            as_file=open('%s/%s.json' % (task_info['iosandbox'],task_info['id']),"w")
            as_file.write(str(task_info))
            try:
                # Insert task record in the GridEngine' queue
                db=self.connect()
                cursor = db.cursor()
                sql=('insert into as_queue (\n'
                     '   task_id       -- Taks reference for this GridEngine queue entry\n'
                     '  ,target_id     -- UsersTracking\' ActiveGridInteraction id reference\n'
					 '  ,target        -- Targeted command executor interface for APIServer Daemon\n'
                     '  ,action        -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...\n'
                     '  ,status        -- Operation status: QUEUED,PROCESSING,PROCESSED,FAILED,DONE\n'
                     '  ,target_status -- GridEngine Job Status: WAITING,SCHEDULED,RUNNING,ABORT,DONE\n'
                     '  ,creation      -- When the action is enqueued\n'
                     '  ,last_change   -- When the record has been modified by the GridEngine last time\n'
                     '  ,action_info   -- Temporary directory path containing further info to accomplish the requested operation\n'
                     ') values (%s,NULL,\'GridEngine\',\'SUBMIT\',\'QUEUED\',NULL,now(),now(),%s);'
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
      getTaskList - Get the list of tasks associated to a user and/or app_id
    """
    def getTaskList(self,user,app_id):
        task_ids = []
        try:
            # Get Task ids preparing the right query (user/app_id)
            db=self.connect()
            cursor = db.cursor()
            if app_id is not None:
                sql=('select id\n'
                 'from task\n'
                 'where app_id = %s\n'
                 '  and user = %s;'
                )
                sql_data=(app_id,user)
            else:
                sql=('select id\n'
                 'from task\n'
                 'where user = %s;'
                )
                sql_data=(user,)
            cursor.execute(sql,sql_data)
            for task_id in cursor:
                task_ids+=[task_id[0],]
        except MySQLdb.Error, e:
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            if cursor  is not None: cursor.close()
            if     db  is not None: db.close()
        return task_ids

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
            sql=('insert into as_queue (\n'
                 '   task_id       -- Taks reference for this GridEngine queue entry\n'
                 '  ,target_id     -- (GridEngine) UsersTracking\' ActiveGridInteraction id reference\n'
				 '  ,target        -- Targeted command executor interface for APIServer Daemon\n'
                 '  ,action        -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...\n'
                 '  ,status        -- Operation status: QUEUED,PROCESSING,PROCESSED,FAILED,DONE\n'
                 '  ,target_status -- GridEngine Job Status: WAITING,SCHEDULED,RUNNING,ABORT,DONE\n'
                 '  ,creation      -- When the action is enqueued\n'
                 '  ,last_change   -- When the record has been modified by the GridEngine last time\n'
                 '  ,action_info   -- Temporary directory path containing further info to accomplish the requested operation\n'
                 ') values (%s,NULL,\'GridEngine\',\'CLEAN\',\'QUEUED\',NULL,now(),now(),%s);'
                )
            sql_data=(task_info['id'],task_info['iosandbox'])
            cursor.execute(sql,sql_data)
            sql=('update task set status=\'CANCELLED\', last_change=now() where id=%s;')
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

"""
--  SQL steps to add an application
START TRANSACTION;
BEGIN;
-- Application
insert into application (id,name,description,creation,enabled)
select max(id)+1, 'ophidia client', 'ophidia client demo application', now(), true from application;

-- Application parameters
insert into application_parameter (app_id,param_id,pname,pvalue)
   select max(id)
  ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
    from application_parameter
    where app_id = (select max(id) from application)) param_id
  ,'jobdesc_executable','/bin/bash'
from application;
insert into application_parameter (app_id,param_id,pname,pvalue)
select max(id)
  ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
    from application_parameter
    where app_id = (select max(id) from application)) param_id
  ,'jobdesc_arguments','ophidia_client.sh'
from application;
insert into application_parameter (app_id,param_id,pname,pvalue)
select max(id)
     ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
      from application_parameter
      where app_id = (select max(id) from application)) param_id
     ,'jobdesc_output','ophidia_client.out'
from application;
insert into application_parameter (app_id,param_id,pname,pvalue)
select max(id)
     ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
      from application_parameter
      where app_id = (select max(id) from application)) param_id
     ,'jobdesc_error','ophidia_client.err'
from application;


-- Application files
insert into application_file (app_id,file_id,file,path,override)
select max(id)
     ,(select if(max(file_id)+1 is NULL, 1, max(file_id)+1)
      from application_file
      where app_id = (select max(id) from application)) file_id
      ,'ophidia_client.sh','/var/applications/ophidia_client'
      ,false
from application;

-- Infrastructure
insert into infrastructure (id,app_id,name,description,creation,enabled)
select max(id)+1
      ,(select max(id) from application)
      ,'ophidia@infn.ct','ophidia client test application'
      ,now()
      ,true
from infrastructure;

-- Infrastructure parameters
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue)
select max(id)
      ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
        from infrastructure_parameter
        where infra_id = (select max(id) from infrastructure)) param_id
      ,'jobservice','ssh://90.147.16.55'
from infrastructure;
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue)
select max(id)
      ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
        from infrastructure_parameter
        where infra_id = (select max(id) from infrastructure)) param_id
      ,'username','ophidia'
from infrastructure;
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue)
select max(id)
      ,(select if(max(param_id)+1 is NULL, 1, max(param_id)+1)
        from infrastructure_parameter
        where infra_id = (select max(id) from infrastructure)) param_id
      ,'password','84g3R=FRm_(bC<FW'
from infrastructure;

COMMIT;
"""
