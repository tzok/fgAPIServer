--  SQL steps to add ophidia application
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
  ,'jobdesc_arguments','ophidia_run.sh'
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
      ,'ophidia_run.sh','/var/applications/ophidia_client'
      ,false
from application;
insert into application_file (app_id,file_id,file,path,override)
select max(id)
     ,(select if(max(file_id)+1 is NULL, 1, max(file_id)+1)
      from application_file
      where app_id = (select max(id) from application)) file_id
      ,'ophidia_helper.py','/var/applications/ophidia_client'
      ,false
from application;
insert into application_file (app_id,file_id,file,path,override)
select max(id)
     ,(select if(max(file_id)+1 is NULL, 1, max(file_id)+1)
      from application_file
      where app_id = (select max(id) from application)) file_id
      ,'oph-credentials.txt','/var/applications/ophidia_client'
      ,false
from application;
insert into application_file (app_id,file_id,file,path,override)
select max(id)
     ,(select if(max(file_id)+1 is NULL, 1, max(file_id)+1)
      from application_file
      where app_id = (select max(id) from application)) file_id
      ,'precip_trend_analysis.json','/var/applications/ophidia_client'
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
      ,'password','<please ask for password>'
from infrastructure;

COMMIT;
