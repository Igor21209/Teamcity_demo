whenever sqlerror exit sql.sqlcode
delete FROM PATCH_STATUS
where PATCH_NAME = 'Jira_8';
exit;