whenever sqlerror exit sql.sqlcode
begin
delete FROM PATCH_STATUS
where PATCH_NAME = 'Jira_8';
end;
exit;