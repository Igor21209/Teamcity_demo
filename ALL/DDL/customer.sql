whenever sqlerror exit sql.sqlcode
declare
   c int;
<<<<<<< HEAD
begin
   select count(*) into c from user_tables where table_name = upper('temporar_table');
   if c = 0 then
        execute immediate 'CREATE TABLE customer (id INT,  last_name varchar(64),   first_name varchar(64),   middle_name varchar(64),   birth_date DATE, address varchar(128))';
   end if;
end;

DECLARE
  v_column_exists number := 0;  
BEGIN
=======
  v_column_exists number := 0;  
begin
   select count(*) into c from user_tables where table_name = upper('customer');
   if c = 0 then
        execute immediate 'CREATE TABLE customer (id INT,  last_name varchar(64),   first_name varchar(64),   middle_name varchar(64),   birth_date DATE, address varchar(128))';
   end if;

>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
  Select count(*) into v_column_exists
    from user_tab_cols
    where upper(column_name) = 'ADDRESS'
      and upper(table_name) = 'CUSTOMER';

  if (v_column_exists = 0) then
<<<<<<< HEAD
      execute immediate 'alter table customer address (address varchar(128))';
  end if;
end;
exit;
=======
      execute immediate 'alter table customer add (address varchar(128))';
  end if;
end;
/
exit;
>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
