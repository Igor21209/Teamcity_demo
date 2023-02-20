from subprocess import Popen, PIPE
import subprocess
import yaml
from yaml.loader import SafeLoader
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
import os


@dataclass
class Commit:
    commit: str = None
    date: datetime = None
    branch: str = None


class Teamcity:
    def __init__(self, user, host, target_dir, path_to_ssh_priv_key, path_to_yaml, path_to_sqlplus, oracle_host, oracle_db, oracle_user, oracle_port, target_branch):
        self.user = user
        self.host = host
        self.target_dir = target_dir
        self.path_to_ssh_priv_key = path_to_ssh_priv_key
        self.path_to_yaml = path_to_yaml
        self.path_to_sqlplus = path_to_sqlplus
        self.oracle_host = oracle_host
        self.oracle_db = oracle_db
        self.oracle_user = oracle_user
        self.oracle_port = oracle_port
        self.target_branch = target_branch


    def runSqlQuery(self, sqlCommand, sqlFile=None):
        if sqlCommand:
            with tempfile.NamedTemporaryFile('w+', encoding='UTF-8', suffix='.sql', dir='/tmp') as fp:
                fp.write(sqlCommand)
                fp.flush()
                sql = bytes(f"@{fp.name}", 'UTF-8')
                return self.executeSqlFile(sql)
        else:
            sql = bytes(f"@{sqlFile}", 'UTF-8')
            return self.executeSqlFile(sql)

    def executeSqlFile(self, sql_command):
        session = Popen([f'{self.path_to_sqlplus}', '-S',
                         f'{self.oracle_user}/{os.environ.get("PASS")}@//{self.oracle_host}:{self.oracle_port}/{self.oracle_db}'],
                        stdin=PIPE, stdout=PIPE,
                        stderr=PIPE)
        session.stdin.write(sql_command)
        if session.communicate():
            unknown_command = re.search('unknown command', session.communicate()[0].decode('UTF-8'))
            if session.returncode != 0:
                return False
                #sys.exit(f'Error while executing sql code in file {sqlCommand}')
            if unknown_command:
                return False
                #sys.exit(f'Error while executing sql code in file {sqlCommand}')
        return session.communicate()

    def yaml_parser(self, path):
        with open(f'{path}', 'r') as f:
            data = yaml.load(f, Loader=SafeLoader)
            return data

    def check_patches(self, patches_for_install, list_of_installed_patches_from_db):
        patches_set = set(list_of_installed_patches_from_db)
        patches_for_install = [p for p in patches_for_install if p in patches_set]
        return patches_for_install

    def check_incorrect_order(self, commits_array, branch_array):
        result_compare_order = False
        commits_list = [commit.branch for commit in commits_array]
        if not commits_list == branch_array:
            result_compare_order = True
        return result_compare_order

    def get_current_branch(self):
        current_branch = self.run_shell_command('git branch --show-current').strip()
        return current_branch

    def log_patch_db_success(self, patch):
        add_to_install_patches = f"""whenever sqlerror exit sql.sqlcode
MERGE INTO PATCH_STATUS USING DUAL ON (PATCH_NAME = '{patch}')
WHEN NOT MATCHED THEN INSERT (PATCH_NAME, INSTALL_DATE, STATUS)
VALUES('{patch}', current_timestamp, 'SUCCESS')
WHEN MATCHED THEN UPDATE SET INSTALL_DATE=current_timestamp, STATUS='SUCCESS';
exit;"""
        self.runSqlQuery(add_to_install_patches)

    def rollback(self, patch, flag, commit=None):
        patch_rollback = f'Patches/{patch}/deploy.yml'
        rollback_skripts = self.yaml_parser(patch_rollback).get('rollback')
        if flag:
            for skript in rollback_skripts:
                query = self.get_commit_version(skript, commit)
                res = self.runSqlQuery(query)
                if not res:
                    sys.exit(f'Error while executing rollback sql code in file {query}')
        else:
            for skript in rollback_skripts:
                res = self.runSqlQuery(None, skript)
                if not res:
                    sys.exit(f'Error while executing rollback sql code in file {skript}')

    def install_release(self, patches_from_deploy_order):
        patches = patches_from_deploy_order.get('patch')
        patches_for_install = self.get_patches_for_install(patches)
        if len(patches_for_install) == 0:
            sys.exit(f'Nothing to install')
        patches_for_install_order = self.check_patches(patches, patches_for_install)
        is_single_patch = not (len(patches_for_install) == 1 and self.get_current_branch() == patches_for_install[0])
        if is_single_patch:
            list_of_commit_objects = self.git_recive_commits()
            check_order_result = self.check_incorrect_order(list_of_commit_objects, patches_for_install_order)
        else:
            list_of_commit_objects = []
            list_of_commit_objects.append(Commit(None, None, patches_for_install[0]))
            check_order_result = False
        if not check_order_result:
            patch_is_installed = True
            for patch in list_of_commit_objects:
                patch_deploy = f'Patches/{patch.branch}/deploy.yml'
                install_order = self.yaml_parser(patch_deploy)
                sql_list = install_order.get('sql')
                sas_list = install_order.get('sas')
                if sql_list:
                    for sql in sql_list:
                        if is_single_patch:
                            query = self.get_commit_version(sql, patch.commit)
                            res = self.runSqlQuery(query)
                            if not res:
                                print(f"Start rollback for patch {patch.branch}")
                                patch_is_installed = False
                                self.rollback(patch.branch, True, patch.commit)
                                break
                        else:
                            res = self.runSqlQuery(None, sql)
                            if not res:
                                print(f"Start rollback for patch {patch.branch}")
                                patch_is_installed = False
                                self.rollback(patch.branch, False)
                                break
                if sas_list:
                    for sas in sas_list:
                        #self.ssh_copy(sas, self.target_dir)
                        path = self.run_shell_command("pwd")
                        self.ansible_copy(f"{path.strip()}/{sas}", self.target_dir)
                if patch_is_installed:
                    self.log_patch_db_success(patch.branch)
                patch_is_installed = True
        else:
            sys.exit(f"Patches order does not match commits order")

    def ansible_copy(self, sourse, dest):
        playbook = """---
- name: copy dir
  hosts: all
  become: yes
  vars:
    - sourse_file : %s
    - dest_file   : %s
  tasks:
  - name: Copy file
    copy: src={{sourse_file}} dest={{dest_file}} mode=777
    """ % (sourse, dest)
        with tempfile.NamedTemporaryFile('w+', encoding='UTF-8', suffix='.yaml', dir='/tmp') as fp:
            fp.write(playbook)
            fp.flush()
            skript = f"ansible-playbook {fp.name}"
            res = self.run_shell_command(skript)
            check = re.search('failed=(\S)', res).group(1)
            if int(check) != 0:
                print(res)
                sys.exit(f'Error while copying {sourse}')
            return res

    def ssh_copy(self, sourse, target):
        dirs = re.split('/', sourse)
        create_dirs = ''
        for i in dirs:
            if i == dirs[-1]:
                break
            create_dirs = create_dirs + i + '/'
        create = re.search('SAS/(.+)', create_dirs)
        if create:
            dir_for_create = create.group(1)
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

    def get_commit_version(self, sql_path, commit):
        command_1 = f'git show {commit}:./{sql_path}'
        sql_exec = Popen(args=command_1,
            stdout=PIPE,
            shell=True)
        sql_command = sql_exec.communicate()[0].decode('UTF-8')
        return sql_command

    def git_recive_commits(self):
        commit_list = []
        all_commits = self.run_shell_command(f'git rev-list --first-parent {self.target_branch}..HEAD')
        all_merges = self.run_shell_command(f'git rev-list --merges --first-parent {self.target_branch}..HEAD')
        merges_list = re.findall('(.+)\n', all_merges)
        if all_commits == all_merges:
            for commit in merges_list:
                branch = f'git show {commit}'
                get_branch = self.run_shell_command(branch)
                date = re.search('Date: (.+)', get_branch).group(1).strip()
                branch_name = re.search('\{\%(.+)\%\}', get_branch).group(1)
                commit_list.append(Commit(commit, date, branch_name))
            commit_list.sort(reverse=False, key=lambda comm: comm.date)
        else:
            sys.exit(f'There are several commits which is not merges in branch {self.get_current_branch()}')
        return commit_list

    def get_patches_for_install(self, patches):
        patches_for_install = []
        query_create_type = """whenever sqlerror exit sql.sqlcode
CREATE OR REPLACE TYPE arr_patch_type IS TABLE OF VARCHAR2(32);
/
exit;"""
        self.runSqlQuery(query_create_type)
        deploy_order = ''
        for patch in patches:
            deploy_order += 'all_patches_list.EXTEND;\n'
            deploy_order += f"all_patches_list(all_patches_list.LAST) := '{patch}';\n"
        query_uninstalled_patches = f"""SET SERVEROUTPUT ON
whenever sqlerror exit sql.sqlcode
DECLARE
  all_patches_list arr_patch_type := arr_patch_type();
  uninstalled_patches arr_patch_type := arr_patch_type();
  installed_patches arr_patch_type := arr_patch_type();
BEGIN
  {deploy_order}
  SELECT PATCH_NAME BULK COLLECT INTO installed_patches FROM PATCH_STATUS
  WHERE PATCH_NAME IN (select * from table(all_patches_list));
  uninstalled_patches := all_patches_list MULTISET EXCEPT installed_patches;
  DBMS_OUTPUT.PUT_LINE('START_RES');
  FOR i IN 1..uninstalled_patches.COUNT LOOP
    DBMS_OUTPUT.PUT_LINE(uninstalled_patches(i));
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('FINISH_RES');
END;
/
exit;"""
        patches_to_install = self.runSqlQuery(query_uninstalled_patches)
        all_patches = re.search('START_RES\n(.+)\nFINISH_RES', patches_to_install[0].decode('UTF-8'), re.S)
        if all_patches:
            patches_for_install = all_patches.group(1).split('\n')
        return patches_for_install

    def start(self):
        data = self.yaml_parser(self.path_to_yaml)
        self.install_release(data)