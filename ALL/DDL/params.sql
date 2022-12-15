whenever sqlerror exit sql.sqlcode
declare
   c int;
begin
   select count(*) into c from user_tables where table_name = upper('params');
   if c = 0 then
<<<<<<< HEAD
        execute immediate 'CREATE TABLE params (param_name varchar(32),  patam_value varchar(64)';
   end if;
end;
exit;
=======
        execute immediate 'CREATE TABLE params (param_name varchar(32),  param_value varchar(64))';
   end if;
end;
exit;
>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
