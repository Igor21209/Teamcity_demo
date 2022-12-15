from subprocess import Popen, PIPE
import subprocess
import yaml
from yaml.loader import SafeLoader
import re
import sys
import tempfile


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
                pass
                #sys.exit(f'Error while executing sql code in file {sqlCommand}')
            if unknown_command:
                pass
                #sys.exit(f'Error while executing sql code in file {sqlCommand}')
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
        patches_for_install = self.get_patches_for_install(patches_1)
        for patch in patches_for_install:
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

    def run_shell_command(self, command):
        process = Popen(args=command, stdout=PIPE, shell=True)
        return process.communicate()[0].decode('UTF-8')

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

    def git(self, patch_name):
        rev_list = f'git rev-list --merges HEAD ^{patch_name}'
        #commits = self.run_shell_command(rev_list).decode('UTF-8')
        # здесь функция парсинга вывода rev-log, которая возвращает список комитов
        test = ['6fa195d81100f2edf27b1d762398699b76c30105', '6170336e96ee220b9fb1e0efef847cc603a67b77']
        for commit in test:
            branch = f'git show {commit}'
            get_branch = self.run_shell_command(branch)
            branch_1 = re.search('Merge: (.+)', get_branch).group(1)
            print(branch_1)
            get_branch_1 = self.run_shell_command(f'git show {branch_1}')
            print(get_branch_1)

            #branch = re.search('\((.+)\)', get_branch).group(1)
            #print(branch, 'HERE I AM!')
            #commit_version = re.search('commit', get_branch_1).group(1)
            #print(commit_version)
            #date = re.search('Date: (.+)', get_branch).group(1).strip()
            #print(date)





    def get_patches_for_install(self, patches):
        patches_for_install = []
        query_1 = "whenever sqlerror exit sql.sqlcode\
        \nCREATE OR REPLACE TYPE arr_patch_type IS TABLE OF VARCHAR2(32);\
        \n/\
        \nexit;"
        with tempfile.NamedTemporaryFile('w+', encoding='UTF-8', suffix='.sql', dir='/tmp') as fp:
            fp.write(query_1)
            fp.seek(0)
            self.runSqlQuery(bytes(f"@{fp.name}", 'UTF-8'))
        deploy_order = str(patches).replace('[', '(').replace(']', ')').strip()
        query_2 = f"SET SERVEROUTPUT ON\
        \nwhenever sqlerror exit sql.sqlcode\
        \nDECLARE\
        \nall_patches_list arr_patch_type := arr_patch_type{deploy_order};\
        \nuninstalled_patches arr_patch_type := arr_patch_type();\
        \ninstalled_patches arr_patch_type := arr_patch_type();\
        \nBEGIN\
        \nSELECT PATCH_NAME BULK COLLECT INTO installed_patches FROM PATCH_STATUS\
        \nWHERE PATCH_NAME IN (select * from table(all_patches_list));\
        \nuninstalled_patches := all_patches_list MULTISET EXCEPT installed_patches;\
        \nFOR i IN 1..uninstalled_patches.COUNT LOOP\
        \nDBMS_OUTPUT.PUT_LINE(uninstalled_patches(i));\
        \nEND LOOP;\
        \nEND;\
        \n/\
        \nexit;"
        with tempfile.NamedTemporaryFile('w+', encoding='UTF-8', suffix='.sql', dir='/tmp') as fp:
            fp.write(query_2)
            fp.seek(0)
            test = self.runSqlQuery(bytes(f"@{fp.name}", 'UTF-8'))
            patches_for_install = re.findall('(.+)\n', test[0].decode('UTF-8'))
            patches_for_install.pop(-1)
        return patches_for_install

    def start(self):
        #data = self.yaml_parser(self.path_to_yaml)
        #self.execute_files(data)

        #test = self.yaml_parser(self.path_to_yaml).get('patch')
        #self.get_pathes_for_insall(test)
        #self.get_commit_version('ALL/DDL/customer.sql')
        #self.get_patches_for_install()

        self.git('Jira_2')








