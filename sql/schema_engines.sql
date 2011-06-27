SELECT  table_schema, engine,
        ROUND(SUM(data_length+index_length)/1024/1024) AS total_mb,
        ROUND(SUM(data_length)/1024/1024) AS data_mb,
        ROUND(SUM(index_length)/1024/1024) AS index_mb,
        COUNT(*) AS tables
FROM  information_schema.tables
GROUP BY table_schema, engine
ORDER BY 3 DESC;
