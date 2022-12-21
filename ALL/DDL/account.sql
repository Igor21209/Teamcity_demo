whenever sqlerror exit sql.sqlcode
declare
   c int;
  v_column_exists number := 0;  
begin
   select count(*) into c from user_tables where table_name = upper('account');
   if c = 0 then
        execute immediate 'CREATE TABLE account (account_id INT,   agreement_id INT, start_date DATE,   final_date DATE,   account_nbr varchar(32),   name varchar(64), branch_name varchar(16))';
   end if;

  Select count(*) into v_column_exists
    from user_tab_cols
    where upper(column_name) = 'BRANCH_NAME'
      and upper(table_name) = 'ACCOUNT';

  if (v_column_exists = 0) then
      execute immediate 'alter table ACCOUNT add (BRANCH_NAME varchar(128))';
  end if;
end;
/
exit;
	
