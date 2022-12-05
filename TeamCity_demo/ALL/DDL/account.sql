whenever sqlerror exit sql.sqlcode
declare
   c int;
begin
   select count(*) into c from user_tables where table_name = upper('temporar_table');
   if c = 0 then
        execute immediate 'CREATE TABLE account (account_id INT,   agreement_id INT, start_date DATE,   final_date DATE,   account_nbr varchar(32),   name varchar(64))';
   end if;
end;
exit;
	
