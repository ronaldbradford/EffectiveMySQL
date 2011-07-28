#!/usr/bin/env python
#
# MySQL StatPack
#
# Copyright (C) 2007 Mark Leith
# (mleith@mysql.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# The GNU General Public License is available at:
# http://www.gnu.org/copyleft/gpl.html

import os
import sys
import getopt
import string
import array
import math
import locale
import time

usage = " usage: ./%s [list of arguments]\n\n" % os.path.basename(sys.argv[0])
usage = usage+" Non-interactive mode (aggregate txt files containing SHOW STATUS snapshots):\n\n"
usage = usage+"   -f --files    	List of statistics files to aggregate (--files=stat1.txt[, stat2.txt..])\n"
usage = usage+" 			Argument must be first within list of arguments, on it's own\n\n"
usage = usage+" Interactive mode (connect to running MySQL server for SHOW STATUS snapshots):\n\n"
usage = usage+"   -h --host			Host for MySQL server to connect to in interactive mode\n"
usage = usage+"   -P --port			Port the MySQL server is running on\n"
usage = usage+"   -S --socket			UNIX domain socket to use (instead of -h and -P)\n"
usage = usage+"   -u --user			User to connect to the MySQL server with\n"
usage = usage+"   -p --password		Password for the user\n"
usage = usage+"   -d --defaults-file		Defaults file to read options from (reads [client] group by default)\n"
usage = usage+"   -i --interval   		Length of each collection interval\n"
usage = usage+"   -c --interval-count		Count of intervals to collect and aggregate\n"
usage = usage+"   -s --status-file		File to output raw SHOW STATUS data to\n\n"
usage = usage+" All modes:\n\n"
usage = usage+"   -r --report-file		File to output generated report(s) to\n"

# Check that there were arguments passed, else print usage statement
if len(sys.argv) < 2:
  print "\n Error: No arguments supplied"
  print usage
  sys.exit(0)

# Set up some defaults for input parameters
files = ''
statFiles = []
statCount = 1
interval = 60
reportFile = 'DEFAULT'
statusFile = 'DEFAULT'

connString = {'host': "localhost", 'port': 3306, 'user': "root", 'passwd': ""}

# Read in options from the command line
letters = 'f:h:P:S:u:p:d:c:i:r:s:'
keywords = ['files=', 'host=', 'port=', 'socket=', 'user=', 'password=', 
    'defaults-file=', 'interval=', 'interval-count=', 'report-file=', 
    'status-file=']

opts, extraparams = getopt.getopt(sys.argv[1:], letters, keywords) 
  
for o,p in opts:
  if o in ['-f', '--files']:
    files = p
    statFiles = files.split(',')
  elif o in ['-h', '--host']:
    connString["host"] = p
  elif o in ['-P', '--port']:
    connString["port"] = p
  elif  o in ['-S', '--socket']:
    connString["unix_socket"] = p
  elif o in ['-u', '--user']:
    connString["user"] = p
  elif o in ['-p', '--password']:
    connString["passwd"] = p
  elif o in ['-d', '--defaults-file']:
    connString["read_default_file"] = p
  elif o in ['-i', '--interval']:
    interval = int(p)
  elif o in ['-c', '--interval-count']:
    statCount = int(p)
  elif o in ['-r', '--report-file']:
    reportFile = p
  elif o in ['-s', '--status-file']:
    statusFile = p
    
# List of SHOW STATUS variables to aggregate
varList = [["Uptime"],["Connections"],["Questions"],["Aborted_clients"], 
    ["Aborted_connects"],["Bytes_received"],["Bytes_sent"], 
    ["Com_insert"],["Com_insert_select"],["Com_update"],
    ["Com_update_multi"],["Com_delete"],["Com_delete_multi"], 
    ["Com_select"],["Created_tmp_tables"],["Created_tmp_disk_tables"], 
    ["Created_tmp_files"],["Key_reads"],["Key_read_requests"], 
    ["Key_writes"],["Key_write_requests"],["Key_blocks_used"], 
    ["Key_blocks_unused"],["Key_blocks_not_flushed"],["Open_tables"], 
    ["Opened_tables"],["Innodb_buffer_pool_reads"], 
    ["Innodb_buffer_pool_read_requests"],["Innodb_buffer_pool_write_requests"],
    ["Innodb_buffer_pool_pages_total"],["Innodb_buffer_pool_pages_free"],
    ["Innodb_buffer_pool_pages_data"],["Innodb_buffer_pool_pages_dirty"],
    ["Innodb_log_writes"],["Innodb_log_write_requests"],["Innodb_log_waits"],
    ["Innodb_os_log_written"],["Innodb_data_read"],["Innodb_data_written"],
    ["Qcache_hits"],["Qcache_inserts"],["Qcache_not_cached"], 
    ["Qcache_lowmem_prunes"],["Qcache_total_blocks"], 
    ["Qcache_queries_in_cache"],["Qcache_free_blocks"],
    ["Handler_read_first"], ["Handler_read_key"], ["Handler_read_next"], 
    ["Handler_read_prev"], ["Handler_read_rnd"], ["Handler_read_rnd_next"], 
    ["Select_scan"], ["Threads_connected"], ["Threads_running"], 
    ["Com_replace"], ["Table_locks_waited"], ["Table_locks_immediate"],
    ["Com_replace_select"], ["Sort_rows"], ["Sort_range"], ["Sort_scan"], 
    ["Sort_merge_passes"], ["Com_commit"],["Com_rollback"],["Com_stmt_close"],
    ["Com_stmt_execute"], ["Com_stmt_fetch"],["Com_stmt_prepare"],
    ["Com_stmt_reset"],["Com_stmt_send_long_data"],["Com_kill"],
    ["Com_flush"],["Com_analyze"],["Com_check"],["Com_optimize"],["Com_repair"],
    ["Prepared_stmt_count"],["Select_full_join"],["Select_full_range_join"],
    ["Threads_created"]]
        
# Print status variable array index
#i = 0
#for word in varList:
#  print str(i) +" "+ varList[i][0]
#  i += 1

# Read each file passed in, and store the variable values within the varList array
# reads files created both with and without table format (mysql -B option or not)
def readFiles(sFiles, sVars):
  for sFile in sFiles:
    try:
      input = file(sFile, 'rb')
      for line in input:
        # process files with a table format output
        if line.find("|") >= 0:
          for word in line.split():
            i = 0
            for var in varList:
              if word.endswith(varList[i][0]):
                line = line[line.find("|", 2):]
                line = line.strip()
                line = line.strip("|")
                line = line.strip()
                varList[i].append(string.atoi(line))
              i += 1
          # process files without a table format output
        elif line.find("|") == -1:
          for word in line.split():
            i = 0 
            for var in varList:
              if word.endswith(varList[i][0]):
                line = line.split()[1]
                varList[i].append(string.atoi(line))
                found = 1
              i += 1
      input.close()
    except IOError:
      print "Error: File %s does not exist" % file
  return

# Connect to a running MySQL server to collect statistics to then output within 
# a report. Works differently to readFiles, in that it always only holds two
# status values within the array, and shifts them after outputting report
def getLiveStats():
  try:
    conn = MySQLdb.connect (**connString)
    cursor = conn.cursor ()
    
    if statusFile != 'DEFAULT':
      sFile = open(statusFile, 'w')
    
    snapsDone = 0
    while (snapsDone <= statCount):

      if statusFile != 'DEFAULT':
        sFile.write(time.ctime(time.time()) + '\n\n')
        
      cursor.execute ("SHOW /*!50000 GLOBAL */ STATUS")

      while (1):
        row = cursor.fetchone ()
        if row == None:
          if statusFile != 'DEFAULT':
            sFile.write('\n')
          break
          
        if statusFile != 'DEFAULT':
          sFile.write(row[0] + '	' + row[1] + '\n')
          
        i = 0        
        for var in varList:
          if len(varList[0]) < 3:
            if row[0] == varList[i][0]:
              varList[i].append(string.atoi(row[1]))
            i += 1
          else:
            if row[0] == varList[i][0]:
              varList[i][2] = string.atoi(row[1])
            i += 1
          
      if len(varList[0]) == 3:
        statPeriods = []
        i = 1
        for periods in range(len(varList[0])-2):
          statPeriods.append((varList[0][i+1] - varList[0][i]))
          i += 1
        genReport(statPeriods)

      snapsDone += 1
      if snapsDone > statCount:
        break
        
      i = 0
      for var in varList:
        try:
          varList[i][1] = varList[i][2]
          i += 1
        except IndexError:
          pass
    
      time.sleep(interval)
      
    if statusFile != 'DEFAULT':
      sFile.close()

    cursor.close ()
    conn.close ()
    return
  except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit (1)

# Format ints nicely for report
def int_format(num):
  return locale.format("%d", num, True)
    
# Format floats nicely for report
def float_format(num, places=2):
  return locale.format("%.*f", (places, num), True)
  
# Format values in to B/K/M/G 
def byte_format(num):
  bsize = ""
  if (num < 1024):
    bsize = bsize + int_format(num) + "B"
    return bsize
  elif (num > 1024 and num < 1048576):
    bsize = bsize + int_format(num/1024) + "K"
    return bsize
  elif (num > 1048576 and num < 1073741824):
    bsize = bsize + int_format(num/1048576) + "M"
    return bsize
  else:
    bsize = bsize + int_format(num/1073741824) + "G"
    return bsize

# Standard template for generic reporting lines 
# (     Name:      Delta x       (x per second)        Total: x)
def reportLine(p, varId, j, altName, bytes):
  if (altName == ''):
    line = "%s: "% varList[varId][0].rjust(27)
  else:
    line = "%s: "% altName.rjust(27)
  try:
    # If bytes is passed in as 0, report raw values
    if (bytes == 0):
      line = line+"%s"% \
        int_format(varList[varId][j+1] - varList[varId][j]).rjust(16)
      line = line+"%s"% \
        float_format((float(varList[varId][j+1]) - varList[varId][j])/p).rjust(25)
      line = line+"%s"% int_format(varList[varId][j+1]).rjust(25)
    # Otherwise we want to use byte_format() to display B/K/M/G formats
    else:
      line = line+"%s"% \
        byte_format(varList[varId][j+1] - varList[varId][j]).rjust(16)
      line = line+"%s"% \
        byte_format((float(varList[varId][j+1]) - varList[varId][j])/p).rjust(25)
      line = line+"%s"% byte_format(varList[varId][j+1]).rjust(25)
  except IndexError:
    line = line+"  Status variable not available in your MySQL version"
  return line
    
# Print a nice time format in the report header for MySQL server uptime
# "Stolen" and converted from the the mysql "status" command
def nice_time(secs):
  dtstr = ""
  if (secs >= 3600.0*24):
    tmp = math.floor(secs/(3600.0*24))
    secs -= 3600.0*24*tmp
    dtstr = dtstr +"%d"%tmp 
    if tmp > 1:
      dtstr = dtstr + " days "
    else:
      dtstr = dtstr + " day "
  if (secs >= 3600.0):
    tmp = math.floor(secs/3600.0)
    secs -= 3600.0*tmp
    dtstr = dtstr +"%d"%tmp 
    if tmp > 1:
      dtstr = dtstr + " hours "
    else:
      dtstr = dtstr + " hour "
  if (secs >= 60.0):
    tmp = math.floor(secs/60.0)
    secs -= 60.0*tmp
    dtstr =  dtstr +"%d"%tmp +" mins "
  return dtstr

def genReport(periods):
  sep = "===================================================================================================="
  reportWidth = 100
  j = 1
  for p in periods:
    print sep
    print ("Uptime: %s"%nice_time(varList[0][j+1]) + \
      "Snapshot Period %d: " %j +"%d minute interval "\
      % (p/60)).center(reportWidth)
    print sep
    print "Variable".rjust(28)+ \
      "	Delta/Percentage 	    Per Second			  Total"
    print sep
    
    print "Database Activity".center(reportWidth)+"\n"+sep+"\n"
    print "Threads Connected:".rjust(28)+"%s" \
      %int_format((varList[53][j+1]-varList[53][j])).rjust(17)+ \
      "%s"%int_format(varList[53][j+1]).rjust(50)
    print "Threads Running:".rjust(28)+"%s" \
      %int_format((varList[54][j+1]-varList[54][j])).rjust(17)+ \
      "%s"%int_format(varList[54][j+1]).rjust(50)
    print reportLine(p, 2, j,'Questions', 0)
    print reportLine(p, 5, j,'Bytes Recieved', 1)
    print reportLine(p, 6, j,'Bytes Sent', 1)
    print reportLine(p, 3, j,'Aborted Clients', 0)
    print reportLine(p, 4, j,'Aborted Connects', 0)+"\n"

    print sep+"\n"+"Statement Activity".center(reportWidth)+"\n"+sep+"\n"
    # Calculate the totals of all statements reported on to get percentages
    tstmts = float(varList[13][j+1]+varList[7][j+1]+varList[9][j+1]+ \
                   varList[11][j+1]+varList[55][j+1] +varList[8][j+1]+ \
                   varList[58][j+1]+varList[10][j+1]+varList[12][j+1]+ \
                   varList[63][j+1]+varList[64][j+1])
    # Hack for low load servers, that might have no statments executed in snapshot
    # saves division by zero errors
    if tstmts == 0:
      tstmts = 1
    print reportLine(p, 13, j,'SELECT', 0) + \
      " (%.2f%%)"% (100*(varList[13][j+1]/tstmts))
    print reportLine(p, 7, j,'INSERT', 0) + \
      " (%.2f%%)"% (100*(varList[7][j+1]/tstmts)) 
    print reportLine(p, 9, j,'UPDATE', 0) + \
      " (%.2f%%)"% (100*(varList[9][j+1]/tstmts))
    print reportLine(p, 11, j,'DELETE', 0) + \
      " (%.2f%%)"% (100*(varList[11][j+1]/tstmts))
    print reportLine(p, 55, j,'REPLACE', 0) + \
      " (%.2f%%)"% (100*(varList[55][j+1]/tstmts))
    print reportLine(p, 8, j,'INSERT ... SELECT', 0) + \
      " (%.2f%%)"% (100*(varList[8][j+1]/tstmts))
    print reportLine(p, 58, j,'REPLACE ... SELECT', 0) + \
      " (%.2f%%)"% (100*(varList[58][j+1]/tstmts))
    print reportLine(p, 10, j,'Multi UPDATE', 0) + \
      " (%.2f%%)"% (100*(varList[10][j+1]/tstmts))
    print reportLine(p, 12, j,'Multi DELETE', 0) + \
      " (%.2f%%)"% (100*(varList[12][j+1]/tstmts))
    print reportLine(p, 63, j,'COMMIT', 0) + \
      " (%.2f%%)"% (100*(varList[63][j+1]/tstmts))
    print reportLine(p, 64, j,'ROLLBACK', 0) + \
      " (%.2f%%)"% (100*(varList[64][j+1]/tstmts))+"\n"
    
    print sep+"\n"+"Prepared Statements".center(reportWidth)+"\n"+sep+"\n"
    print reportLine(p, 77,j,'Prepared Statement Count', 0)
    print reportLine(p, 68,j,'PREPARE', 0)
    print reportLine(p, 66,j,'EXECUTE', 0)
    print reportLine(p, 65,j,'DEALLOCATE PREPARE', 0)
    print reportLine(p, 67,j,'Fetch Roundtrips', 0)
    print reportLine(p, 70,j,'Send Long Data', 0)+"\n"
    
    print sep+"\n"+"Admin Commands".center(reportWidth)+"\n"+sep+"\n"
    print reportLine(p, 71,j,'KILL', 0)
    print reportLine(p, 72,j,'FLUSH', 0)
    print reportLine(p, 73,j,'ANALYZE TABLE', 0)
    print reportLine(p, 75,j,'OPTIMIZE TABLE', 0)
    print reportLine(p, 74,j,'CHECK TABLE', 0)
    print reportLine(p, 76,j,'REPAIR TABLE', 0)+"\n"
    
    print sep+"\n"+"Thread Cache".center(reportWidth)+"\n"+sep+"\n"
    print "Thread Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      float(100-((varList[80][j+1]/varList[1][j+1])*100))
    print reportLine(p, 1,j,'Connections', 0)
    print reportLine(p, 80,j,'Threads Created', 0)+"\n"
    
    print sep+"\n"+"Table Cache".center(reportWidth)+"\n"+sep+"\n"
    print "table_cache Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      ((float(varList[24][j+1])/(varList[25][j+1]+1))*100)
    print reportLine(p, 24,j,'Open Tables', 0)
    print reportLine(p, 25,j,'Opened Tables', 0)+"\n"
    
    print sep+"\n"+"MyISAM Key Cache".center(reportWidth)+"\n"+sep+"\n"
    # (100-((Key_reads/(Key_read_requests+1))*100)
    print "Cache Read Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      (100-((float(varList[17][j+1])/(varList[18][j+1]+1))*100))
    # (100-(Key_writes/(Key_write_requests + 1))*100)
    print "Cache Write Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      (100-((float(varList[19][j+1])/(varList[20][j+1]+1))*100))
    print "Memory Used:".rjust(28)+"%s" \
      %byte_format(varList[21][j+1]-varList[21][j]).rjust(17) + \
      "%s"%byte_format(varList[21][j+1]).rjust(50)
    # Key_blocks_unused not available within 4.0
    try:
        print "Memory Free:".rjust(28)+"%s" \
          %byte_format(varList[22][j+1]-varList[22][j]).rjust(17) + \
          "%s"%byte_format(varList[22][j+1]).rjust(50)
    except IndexError:
        print "Memory Free:".rjust(28)+ \
          "  Status variable not available in your MySQL version"
    print reportLine(p, 17,j,'Key Reads', 0)
    print reportLine(p, 18,j,'Key Read Requests', 0)
    print reportLine(p, 19,j,'Key Writes', 0)
    print reportLine(p, 20,j,'Key Write Requests', 0)
    print reportLine(p, 23,j,'Blocks Not Flushed', 0)+"\n"

    print sep+"\n"+"InnoDB Buffer Pool".center(reportWidth)+"\n"+sep+"\n"
    try:
        print "Buffer Pool Read Efficiency:".rjust(28)+"%s%%".rjust(14)% \
          float_format(100-((float(varList[26][j+1])/(varList[27][j+1] + 1))*100))
        print "Memory Total:".rjust(28)+"%s"\
            %byte_format((varList[29][j+1]-varList[29][j])*16384).rjust(17) + \
          "%s"%byte_format(varList[29][j]*16384).rjust(50)
        print "Memory Free:".rjust(28)+"%s"\
            %byte_format((varList[30][j+1]-varList[30][j])*16384).rjust(17) + \
          "%s"%byte_format(varList[30][j]*16384).rjust(50)
        print "Memory Data:".rjust(28)+"%s" \
            %byte_format((varList[31][j+1]-varList[31][j])*16384).rjust(17) + \
          "%s"%byte_format(varList[31][j]*16384).rjust(50)
        print "Memory Dirty:".rjust(28)+"%s" \
            %byte_format((varList[32][j+1]-varList[32][j])*16384).rjust(17) + \
          "%s"%byte_format(varList[32][j]*16384).rjust(50)
        print "Data Read:".rjust(28)+"%s" \
            %byte_format(varList[37][j+1]-varList[37][j]).rjust(17) + \
          "%s"%byte_format(varList[37][j+1]).rjust(50)
        print "Data Written:".rjust(28)+"%s" \
            %byte_format((varList[38][j+1]-varList[38][j])/1024).rjust(17)+\
          "%s"%byte_format(varList[38][j+1]).rjust(50)
        print reportLine(p, 26,j,'Buffer Pool Reads', 0)
        print reportLine(p, 27,j,'Buffer Pool Read Requests', 0)
        print reportLine(p, 28,j,'Buffer Pool Write Requests', 0)+"\n"
    except IndexError:
        print "MySQL Version does not support InnoDB status variables (Available in MySQL 5.0)\n"
    
    print sep+"\n"+"InnoDB Log Files".center(reportWidth)+"\n"+sep+"\n"
    try:
        print "Log Data Written:".rjust(28)+"%s" \
          %byte_format(varList[36][j+1]-varList[36][j]).rjust(17) + \
          "%s"%byte_format(varList[36][j+1]).rjust(50)
        print reportLine(p, 33,j,'Log Writes', 0)
        print reportLine(p, 34,j,'Log Write Requests', 0)
        print reportLine(p, 35,j,'Log Waits', 0)+"\n"
    except IndexError:
        print "MySQL Version does not support InnoDB status variables (Available in MySQL 5.0)\n"
    
    print sep+"\n"+"Query Cache".center(reportWidth)+"\n"+sep+"\n"
    # ((Qcache_hits/(Qcache_hits + Com_select + 1))*100)
    print "QCache Hits / SELECT:".rjust(28)+"%.2f%%".rjust(17)% \
      ((float(varList[39][j+1])/(varList[13][j+1]+varList[39][j+1]+1))*100)
    # ((Qcache_hits/(Qcache_inserts+Qcache_hits+1))*100)
    print "QCache Hit/Qcache Insert:".rjust(28)+"%.2f%%".rjust(17)% \
      ((float(varList[39][j+1])/(varList[39][j+1]+varList[40][j+1]+1))*100)
    # ((Qcache_hits/(Com_insert+Com_update+Com_delete+Com_insert_select+Com_replace+1)
    print "Qcache Hits/Invalidations:".rjust(28)+"%.2f%%".rjust(17)% \
      (((varList[39][j+1])/(varList[7][j+1]+varList[9][j+1] + \
         varList[11][j+1]+varList[8][j+1]+varList[55][j+1]+1)))
    print reportLine(p, 13,j,'SELECTs', 0)
    print reportLine(p, 39,j,'Query Cache Hits', 0)
    print reportLine(p, 40,j,'Query Cache Inserts', 0)
    print reportLine(p, 41,j,'Queries Not Cached', 0)
    print reportLine(p, 42,j,'Cache Low Memory Prunes', 0)
    print reportLine(p, 43,j,'Total Cache Blocks', 0)
    print reportLine(p, 44,j,'Queries In Cache', 0)
    print reportLine(p, 45,j,'Cache Free Blocks', 0)+"\n"
    
    print sep+"\n"+"Index Usage".center(reportWidth)+"\n"+sep+"\n"
    
    # Sum all of the Handler_* variables to compute percentages
    rowsRead = float(varList[46][j+1]+varList[47][j+1]+varList[48][j+1] \
                    +varList[49][j+1]+varList[50][j+1]+varList[51][j+1])
    
    print "Index Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      (100-(((float(varList[50][j+1])+varList[51][j+1])/rowsRead)*100))
    print reportLine(p, 46,j,'Full Index Scans', 0)
    print reportLine(p, 52,j,'Full Table Scans', 0)
    print reportLine(p, 78,j,'Full Join Scans', 0)
    print reportLine(p, 46,j,'', 0) + " (%.2f%%)"% (100*(varList[46][j+1]/rowsRead))
    print reportLine(p, 47,j,'', 0) + " (%.2f%%)"% (100*(varList[47][j+1]/rowsRead))
    print reportLine(p, 48,j,'', 0) + " (%.2f%%)"% (100*(varList[48][j+1]/rowsRead))
    print reportLine(p, 49,j,'', 0) + " (%.2f%%)"% (100*(varList[49][j+1]/rowsRead))
    print reportLine(p, 50,j,'', 0) + " (%.2f%%)"% (100*(varList[50][j+1]/rowsRead))
    print reportLine(p, 51,j,'', 0) + " (%.2f%%)"% (100*(varList[51][j+1]/rowsRead))+"\n"

    print sep+"\n"+"Temporary Space".center(reportWidth)+"\n"+sep+"\n"
    # (100-((Created_tmp_disk_tables/Created_tmp_tables)*100))
    print "tmp_table_size Efficiency:".rjust(28)+"%.2f%%".rjust(17)% \
      (100-((float(varList[15][j+1])/(varList[14][j+1]+1))*100))
    print reportLine(p, 14,j,'Memory Temp Tables', 0)
    print reportLine(p, 15,j,'Disk Temp Tables', 0)
    print reportLine(p, 16,j,'Temp Files', 0)+"\n"

    print sep+"\n"+"Lock Contention".center(reportWidth)+"\n"+sep+"\n"
    print "Percent of Locks Waited:".rjust(28)+"%.2f%%".rjust(18)% \
      ((float(varList[56][j+1])/(varList[56][j+1]+varList[57][j+1]+1))*100)
    print reportLine(p, 56,j,'Table Locks Waited', 0)
    print reportLine(p, 57,j,'Table Locks Immediate', 0)+"\n"
    
    print sep+"\n"+"Sorting".center(reportWidth)+"\n"+sep+"\n"
    print reportLine(p, 59,j,'Rows Sorted', 0)
    print reportLine(p, 60,j,'Sort Range', 0)
    print reportLine(p, 61,j,'Sort Scan', 0)
    print reportLine(p, 62,j,'Sort Merge Passes', 0)
    print reportLine(p, 79,j,'Full Range Joins', 0)+"\n"
    j += 1

def main():
  # Set locale to en_US for use in int_format() and float_format()
  locale.setlocale(locale.LC_NUMERIC, '')
  
  if reportFile != 'DEFAULT':
    rFile = open(reportFile, 'w')
    sys.stdout = rFile

  # "Non-interactive Mode" - if --files passed, run through the list of files
  # and generate one or multiple reports
  if len(files) > 0 : 

    readFiles(statFiles, varList)

    snapCnt = (len(varList[0]) - 1)
    print "\nNumber of Snapshots: %d\n" % snapCnt

    statPeriods = []
    i = 1
    for periods in range(len(varList[0])-2):
      statPeriods.append((varList[0][i+1] - varList[0][i]))
      i += 1

    genReport(statPeriods)
    
  # "Interactive Mode"  - connect to a running server and gather statistics
  else:
  
    if reportFile != 'DEFAULT':
      rFile = open(reportFile, 'w')
      sys.stdout = rFile
    
    getLiveStats()
    
  if reportFile != 'DEFAULT':
    rFile.close()

if __name__ == "__main__":
    main()
