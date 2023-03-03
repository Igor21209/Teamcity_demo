whenever sqlerror exit sql.sqlcode
delete FROM PATCH_STATUS
<<<<<<< HEAD
where PATCH_NAME = 'Jira_8';
=======
where PATCH_NAME = 'Jira_7';
>>>>>>> Jira_8
exit;