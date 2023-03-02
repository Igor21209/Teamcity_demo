whenever sqlerror exit sql.sqlcode
delete FROM PATCH_STATUS
<<<<<<< HEAD
where PATCH_NAME = 'Jira_7';
=======
where PATCH_NAME = 'Jira_8';
>>>>>>> Jira_7
exit;