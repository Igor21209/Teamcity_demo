whenever sqlerror exit sql.sqlcode
delete from params
where param_name='param_2';
insert into params (param_name, param_value)
select 'param_2', 'prama_value_2' from dual;
exit;
	