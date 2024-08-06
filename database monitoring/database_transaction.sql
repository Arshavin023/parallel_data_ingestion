--To get a snapshot of all current activities, including transactions, you can run:

SELECT pid, usename, datname, state, query, query_start
FROM pg_stat_activity;

--Filter for Active Transactions:
--If you're only interested in active transactions, you can filter by the state column:

SELECT pid,query, query_start 
FROM pg_stat_activity WHERE state = 'active'
AND query ilike '%call%' order by query_start desc;

-- Terminate TRANSACTION
select pg_terminate_backend(<pid>);
select pg_terminate_backend(<pid>);

--For more detailed information about locks and waits, you might also want to look at the pg_locks view. 
--You can join it with pg_stat_activity to see which transactions are holding or waiting for locks:

SELECT a.pid,a.usename,a.datname,a.state,a.query,a.query_start,l.mode,l.granted
FROM pg_stat_activity a
LEFT JOIN pg_locks l ON a.pid = l.pid
WHERE a.state = 'active';

--Long-Running Queries:
--To find queries that have been running for a long time, you can use:

SELECT pid, usename, datname, state, query, query_start
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '5 minutes';  -- Adjust the interval as needed
  
  

--top ten transactions
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

  
alter 
  