from subprocess import Popen, PIPE
import subprocess
import yaml
from yaml.loader import SafeLoader
import re
import sys


class Teamcity:
    def __init__(self, user, host, target_dir, path_to_ssh_priv_key, path_to_yaml, path_to_sqlplus, oracle_host, oracle_db, oracle_user):
        self.user = user
        self.host = host
        self.target_dir = target_dir
        self.path_to_ssh_priv_key = path_to_ssh_priv_key
        self.path_to_yaml = path_to_yaml
        self.path_to_sqlplus = path_to_sqlplus
        self.oracle_host = oracle_host
        self.oracle_db = oracle_db
        self.oracle_user = oracle_user

    def runSqlQuery(self, sqlCommand):
        session = Popen([f'{self.path_to_sqlplus}', '-S',
                         f'{self.oracle_user}/{self.get_env_variable("echo $PASS")}@//{self.oracle_host}:1521/{self.oracle_db}'], stdin=PIPE, stdout=PIPE,
                        stderr=PIPE)
        session.stdin.write(sqlCommand)
        if session.communicate():
            unknown_command = re.search('unknown command', session.communicate()[0].decode('UTF-8'))
            if session.returncode != 0:
                sys.exit(f'Error while executing sql code in file {sqlCommand}')
            if unknown_command:
                sys.exit(f'Error while executing sql code in file {sqlCommand}')
        return session.communicate()

    def get_env_variable(self, command):
        process = Popen(
            args=command,
            stdout=PIPE,
            shell=True
        )
        return process.communicate()[0].decode('UTF-8').strip()

    def yaml_parser(self, path):
        with open(f'{path}', 'r') as f:
            data = yaml.load(f, Loader=SafeLoader)
            return data

    def execute_files(self, patches):
        patches_1 = patches.get('patch')
        for patch in patches_1:
            if patch:
                pars = f'Patches/{patch}/deploy.yml'
                data = self.yaml_parser(pars)
                sql = data.get('sql')
                sas = data.get('sas')
                if sql:
                    for q in sql:
                        query = self.get_commit_version(q)
                        #q = f'@{q}'
                        #byte = bytes(q, 'UTF-8')
                        self.runSqlQuery(query)
                if sas:
                    for s in sas:
                        self.ssh_copy(s, self.target_dir)

    def ssh_copy(self, sourse, target):
        dirs = re.split('/', sourse)
        create_dirs = ''
        for i in dirs:
            if i == dirs[-1]:
                break
            create_dirs = create_dirs + i + '/'
        create = re.search('(SAS/).+', create_dirs)
        if create:
            dir_for_create = create.group(0)[4:]
            dirs = subprocess.run(
                ['ssh', '-i', f'{self.path_to_ssh_priv_key}', f'{self.user}@{self.host}', 'mkdir', '-p',
                 f'{target + dir_for_create}'])
            if dirs.returncode != 0:
                sys.exit('Error while making directories on the server')
            files = subprocess.run(
                ['scp', '-i', f'{self.path_to_ssh_priv_key}', '-r', f'{sourse}',
                 f'{self.user}@{self.host}:{target + dir_for_create}'])
            if files.returncode != 0:
                sys.exit('Error while copying file on the server')
        else:
            files = subprocess.run(
                ['scp', '-i', f'{self.path_to_ssh_priv_key}', '-r', f'{sourse}',
                 f'{self.user}@{self.host}:{target}'])
            if files.returncode != 0:
                sys.exit('Error while copying file on the server')
        create_dirs = ''

    def get_pathes_for_insall(self, pathes_from_deply_order):
        count = 0
        q = ""
        for i in pathes_from_deply_order:
            q += f"Ret({count}) := '{i}';\n"
            count += 1
        count = 0
        sql = f'''
CREATE OR REPLACE PACKAGE BODY My_Types IS
FUNCTION Init_My_AA RETURN My_AA IS
Ret My_AA;
  BEGIN
{q}
  RETURN Ret;
  END Init_My_AA;
END My_Types;
        '''
        query = f'@{sql}'
        byte = bytes(query, 'UTF-8')
        self.runSqlQuery(byte)
        
    def get_commit_version(self, sql_path):
        command = f'git log ./{sql_path}'
        commit_version = Popen(args=command,
            stdout=PIPE,
            shell=True)
        output = commit_version.communicate()[0].decode('UTF-8').strip()
        res = re.search('commit (.+)\n', output)
        command_1 = f'git show {res.group(1)}:./{sql_path}'
        sql_exec = Popen(args=command_1,
            stdout=PIPE,
            shell=True)
        sql_command = sql_exec.communicate()[0]
        return sql_command

    def get_patches_for_install(self):
        patches = self.yaml_parser(self.path_to_yaml).get('patch')
        query_1 = 'whenever sqlerror exit sql.sqlcode CREATE OR REPLACE TYPE arr_patch_type IS TABLE OF VARCHAR2(32); exit;'
        self.runSqlQuery(bytes(query_1, 'UTF-8'))
        deploy_order = str(patches).replace('[', '(').replace(']', ')')
        query_2 = f'''
        SET SERVEROUTPUT ON
        whenever sqlerror exit sql.sqlcode
        DECLARE
          all_patches_list arr_patch_type := arr_patch_type{deploy_order};
          uninstalled_patches arr_patch_type := arr_patch_type();
          installed_patches arr_patch_type := arr_patch_type();
        BEGIN
          SELECT PATCH_NAME BULK COLLECT INTO installed_patches FROM PATCH_STATUS
          WHERE PATCH_NAME IN (select * from table(all_patches_list));
          uninstalled_patches := all_patches_list MULTISET EXCEPT installed_patches;
          FOR i IN 1..uninstalled_patches.COUNT LOOP
            DBMS_OUTPUT.PUT_LINE(uninstalled_patches(i));
          END LOOP;
        END;  
        exit;
        '''
        test = self.runSqlQuery(bytes(query_2, 'UTF-8'))
        print(test[0].decode('UTF-8'))



    def start(self):
        #data = self.yaml_parser(self.path_to_yaml)
        #self.execute_files(data)

        #test = self.yaml_parser(self.path_to_yaml).get('patch')
        #self.get_pathes_for_insall(test)
        #self.get_commit_version('ALL/DDL/customer.sql')
        self.get_patches_for_install()








