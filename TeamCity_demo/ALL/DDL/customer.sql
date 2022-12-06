whenever sqlerror exit sql.sqlcode
declare
   c int;
  v_column_exists number := 0;  
begin
   select count(*) into c from user_tables where table_name = upper('customer');
   if c = 0 then
        execute immediate 'CREATE TABLE customer (id INT,  last_name varchar(64),   first_name varchar(64),   middle_name varchar(64),   birth_date DATE, address varchar(128))';
   end if;

  Select count(*) into v_column_exists
    from user_tab_cols
    where upper(column_name) = 'ADDRESS'
      and upper(table_name) = 'CUSTOMER';

  if (v_column_exists = 0) then
      execute immediate 'alter table customer add (address varchar(128))';
  end if;
end;
/
exit;
