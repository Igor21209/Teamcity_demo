whenever sqlerror exit sql.sqlcode
declare
   c int;
begin
   select count(*) into c from user_tables where table_name = upper('customer');
   if c = 0 then
        execute immediate 'CREATE TABLE customer (id INT,  last_name varchar(64),   first_name varchar(64),   middle_name varchar(64),   birth_date DATE)';
   end if;
end;
exit;