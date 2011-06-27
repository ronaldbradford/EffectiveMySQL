SELECT table_schema,table_name, table_rows,
       ROUND((data_length+index_length)/1024/1024) AS total_mb,
       ROUND(data_length/1024/1024) AS data_mb,
       ROUND(index_length/1024/1024) AS index_mb
FROM INFORMATION_SCHEMA.TABLES
WHERE engine='InnoDB';

