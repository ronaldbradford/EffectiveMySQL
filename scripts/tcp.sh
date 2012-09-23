sudo date
# password
export DT=`date +%y%m%d.%H%M%S`  
sudo /usr/sbin/tcpdump -i any port 3306 -s 65535  -x -nn -q -tttt -c 10000 > ${DT}.tcp  
./mk-query-digest --type tcpdump --limit 100%:50 ${DT}.tcp > ${DT}.out
more ${DT}.out

exit 0
