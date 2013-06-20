#!/bin/sh

[ -z "${TMP_DIR}" ] && TMP_DIR=/tmp
TMP_FILE=${TMP_DIR}/binlog.txt.$$

LOGFILE=$1
shift
ARGS=$*
BINLOG=`grep "^log.bin" /etc/my.cnf | cut -d'=' -f2`
DIR=`dirname ${BINLOG}`
[ -z "${LOGFILE}" ] && echo "ERROR: Specify Binary Log (in $DIR) to analyze" &&  ls -ltr ${DIR} | tail -5 && exit 1

mysqlbinlog ${ARGS} ${LOGFILE} \
| sed -e "s/\/\*.*\*\///;s/^ //" | grep -i -e "^update" -e "^insert" -e "^delete" -e "^replace" -e "^alter"  | \
   cut -c1-100 | tr '[A-Z]' '[a-z]' |  \
   sed -e "s/\t/ /g;s/\`//g;s/(.*$//;s/ set .*$//;s/ as .*$//;s/ join .*$//;s/ values .*$//;" | sed -e "s/ where .*$//;s/ignore //g;s/ inner//g;s/ left//g;s/ right//g;s/ from//g;s/ into//g" |  \
   sed -e "s/ \w.*\.\*//" |  awk '{ print $1,$2 }' | \
   sort | uniq -c | sort -nr  > ${TMP_FILE}

TOTAL=`awk 'BEGIN {total=0}{total=total+ $1}END{print total}' ${TMP_FILE}`
echo "%    ${TOTAL} ALL QUERIES"
head -50 ${TMP_FILE} | awk -v TOTAL=${TOTAL} '{printf("%.2f %s\n",$1*100.0/TOTAL, $0)}'
echo "Details in ${TMP_FILE}"
exit 0
