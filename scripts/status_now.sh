#!/bin/sh

error() {
  echo "ERROR: $*"
  exit 1
}


[ -z "${MYSQL_AUTHENTICATION}" ] && error "There is no MYSQL_AUTHENTICATION to execute mysql commands"
[ -z "${MYSQL_HOME}" ] && error "MYSQL_HOME must be specified"
[ -z `which mysqladmin` ] && error "mysqladmin not in path, \$MYSQL_HOME/bin should be added to PATH"

 
mysqladmin ${MYSQL_AUTHENTICATION} -r -i 1 extended-status | grep -v " | 0 "

return 0
