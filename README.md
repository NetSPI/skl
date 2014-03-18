skl
===

strace keylogger Proof of Concept.

This python code runs strace against all the ssh and sshd processes and parses
the output and saves it to log files.  The default location is ~/tmp/.skl

This code does not make any attempt to hide itself.
