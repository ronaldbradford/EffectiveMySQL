#!/bin/sh

LOGFILE=$1
[ -z "{$LOGFILE}" ] && echo "ERROR: Specify Binary Log to analyze" && exit 1

mysqlbinlog $LOGFILE | grep -i -e "^update" -e "^insert" -e "^delete" -e "^replace" -e "^alter"  | \
   cut -c1-100 | tr '[A-Z]' '[a-z]' |  \
   sed -e "s/\t/ /g;s/\`//g;s/(.*$//;s/ set .*$//;s/ as .*$//" | sed -e "s/ where .*$//" |  \
   sort | uniq -c | sort -nr  

#awk 'BEGIN {total=0}{total=total+ $1}END{print total}' file
exit 0

