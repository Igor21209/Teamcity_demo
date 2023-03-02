whenever sqlerror exit sql.sqlcode
delete FROM PATCH_STATUS
where PATCH_NAME = 'Jira_7';
exit;