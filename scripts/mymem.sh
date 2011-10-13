#!/bin/sh


DELAY=$1
[ -z "${DELAY}" ] && DELAY=5


echo "Date,time,mysqlrss,mysqlvsz,"`cat /proc/meminfo | awk '{printf("%s,",$1)}'`
echo ""
while [ : ]
do
DATETIME=`date +%Y%m%d,%H%M%S`
MYSQL=`ps -eopid,fname,rss,vsz,user,command | grep " mysqld " | grep -v grep | awk '{printf("%s,%s", $3,$4)}'`
MEMINFO=`cat /proc/meminfo | awk '{printf("%s,",$2)}'`
echo "${DATETIME},${MYSQL},${MEMINFO}"
sleep ${DELAY}

done

exit 0

