whenever sqlerror exit sql.sqlcode
declare
   c int;
begin
   select count(*) into c from user_tables where table_name = upper('temporar_table');
   if c = 0 then
        execute immediate 'CREATE TABLE params (param_name varchar(32),  patam_value varchar(64)';
   end if;
end;
exit;