whenever sqlerror exit sql.sqlcode
delete from params
where param_name='param_1';
insert into params (param_name, param_value)
select 'param_1', 'prama_value_1' from dual;
exit;
	