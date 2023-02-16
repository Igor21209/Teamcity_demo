whenever sqlerror exit sql.sqlcode
begin
select * FROM ATCH_STATUS;
end;
exit;