whenever sqlerror exit sql.sqlcode
declare
   c int;
<<<<<<< HEAD
=======
  v_column_exists number := 0;  
>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
begin
   select count(*) into c from user_tables where table_name = upper('account');
   if c = 0 then
        execute immediate 'CREATE TABLE account (account_id INT,   agreement_id INT, start_date DATE,   final_date DATE,   account_nbr varchar(32),   name varchar(64), branch_name varchar(16))';
   end if;
<<<<<<< HEAD
end;

DECLARE
  v_column_exists number := 0;  
BEGIN
=======

>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
  Select count(*) into v_column_exists
    from user_tab_cols
    where upper(column_name) = 'BRANCH_NAME'
      and upper(table_name) = 'ACCOUNT';

  if (v_column_exists = 0) then
<<<<<<< HEAD
      execute immediate 'alter table ACCOUNT add (BRANCH_NAME varchar(128))';
  end if;
end;
exit;
	
=======
      execute immediate 'alter table ACOUNT add (BRANCH_NAME varchar(128))';
  end if;
end;
/
exit;	
>>>>>>> e1e3aa5c7139d6091c649165199cf20d862a9aa2
