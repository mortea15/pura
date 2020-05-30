#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getopt
import os
import sys

import pura
from pura.helpers.logger import increase_log_level, log_to_file
from pura.helpers.logger import rootLogger as logger

current = os.path.realpath(os.path.dirname(__file__))
APPNAME = 'pura'


INDENT = '  '
HELPMSG = f'''usage: {APPNAME} [-v] [-l]
    General options:
    {INDENT * 1}-v, --verbose       {INDENT * 2}Increase verbosity (can be used several times, e.g. -vvv).
    {INDENT * 1}-l, --log-file      {INDENT * 2}Write log events to the file `{APPNAME}.log`.
    {INDENT * 1}--help              {INDENT * 2}Print this message.
'''


def main():
    CONFIG = {}

    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, 'hlv', ['help', 'log-file', 'verbose'])
    except getopt.GetoptError:
        print(HELPMSG)
        sys.exit(2)

    """
    Increase verbosity
    """
    opts_v = len(list(filter(lambda opt: opt == ('-v', ''), opts)))
    if opts_v > 4:
        opts_v = 4
    v = 0
    while v < opts_v:
        increase_log_level()
        v += 1
    
    """
    Log to file
    """
    if v > 0:
        enable_logfile = list(filter(lambda opt: opt[0] in ('-l', '--log-file'), opts))
        if enable_logfile:
            log_to_file()
    
    for opt, arg in opts:
        if opt == '--help':
            print(HELPMSG)
            sys.exit(0)

    emls = pura.fetch_emails()
    #emls = pura.fetch_testdata()
    for eml in emls:
        print(eml.subject)
        pura.handle_event(eml)
    

if __name__ == '__main__':
    main()
