#!/usr/bin/env python2
# coding:utf-8

import os
import sys
import time
import signal
import argparse
import logging
import functools

from subprocess import call, PIPE
from threading import Thread
from datetime import datetime
from collections import Counter

from qsub import qsub
from version import __version__


class ParseSingal(Thread):
    def __init__(self):
        super(ParseSingal, self).__init__()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def run(self):
        time.sleep(1)

    def signal_handler(self, signum, frame):
        stillrunjob = qjobs.jobqueue.queue
        if clear:
            pid = os.getpid()
            gid = os.getpgid(pid)
            for jn in stillrunjob:
                if jn.status in ["error", "success"]:
                    continue
                jn.status = "killed"
                qjobs.logger.info("job %s status killed", jn.name)
            sumJobs(qjobs)
            call('qdel "*_%d"' % os.getpid(),
                 shell=True, stderr=PIPE, stdout=PIPE)
            call("kill -9 -%d" % gid, shell=True, stderr=PIPE, stdout=PIPE)
        else:
            for jn in stillrunjob:
                if jn.status in ["error", "success"]:
                    continue
                jn.status += "-but-exit"
                qjobs.logger.info("job %s status %s", jn.name, jn.status)
            sumJobs(qjobs)
        sys.exit(signum)


def LogExc(f):
    @functools.wraps(f)
    def wrapper(*largs, **kwargs):
        try:
            res = f(*largs, **kwargs)
        except Exception, e:
            logging.getLogger().exception(e)
            os.kill(os.getpid(), 15)
        return res
    return wrapper


def parseArgs():
    parser = argparse.ArgumentParser(
        description="For manger submit your jobs in a job file.")
    parser.add_argument("-n", "--num", type=int,
                        help="the max job number runing at the same time, default: 1000", default=1000, metavar="<int>")
    parser.add_argument("-j", "--jobfile", type=str, required=True,
                        help="the input jobfile", metavar="<jobfile>")
    parser.add_argument('-i', '--injname', help="job names you need to run, default: all jobnames of you job file",
                        nargs="*", type=str, metavar="<str>")
    parser.add_argument('-s', '--start', help="job beginning with the number(0-base) you given, 0 by default",
                        type=int, default=0, metavar="<int>")
    parser.add_argument('-e', '--end', help="job ending with the number you given, last job by default",
                        type=int, metavar="<int>")
    parser.add_argument('-r', '--resub', help="rebsub you job when error, 0 or minus means do not re-submit, 3 times by default",
                        type=int, default=3, metavar="<int>")
    parser.add_argument('-ivs', '--resubivs', help="rebsub interval seconds, 2 by default",
                        type=int, default=2, metavar="<int>")
    parser.add_argument("-m", '--mode', type=str, default="sge", choices=[
                        "sge", "localhost"], help="the mode to submit your jobs, 'sge' by default, if no sge installed, always localhost.")
    parser.add_argument("-nc", '--noclean', action="store_false", help="whether to clean all jobs or subprocess created by this programe when the main process exits, default: clean.",
                        default=True)
    parser.add_argument("--strict", action="store_true", default=False,
                        help="use strict to run. Means if any errors occur, clean all jobs and exit programe. off by default")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='log debug info', default=False)
    parser.add_argument("-l", "--log", type=str,
                        help='append log info to file, sys.stdout by default', metavar="<file>")
    parser.add_argument('-v', '--version',
                        action='version', version="%(prog)s v" + __version__)
    return parser.parse_args()


def Mylog(logfile=None, level="info", name=None):
    logger = logging.getLogger(name)
    if level.lower() == "info":
        logger.setLevel(logging.INFO)
        f = logging.Formatter(
            '[%(levelname)s %(asctime)s] %(message)s')
    elif level.lower() == "debug":
        logger.setLevel(logging.DEBUG)
        f = logging.Formatter(
            '[%(levelname)s %(threadName)s %(asctime)s %(funcName)s(%(lineno)d)] %(message)s')
    if logfile is None:
        h = logging.StreamHandler(sys.stdout)  # default: sys.stderr
    else:
        h = logging.FileHandler(logfile, mode='w')
    h.setFormatter(f)
    logger.addHandler(h)
    return logger


def sumJobs(qjobs):
    run_jobs = qjobs.jobs
    has_success_jobs = qjobs.has_success
    error_jobs = [j for j in run_jobs if j.status == "error"]
    success_jobs = [j for j in run_jobs if j.status == 'success']

    logger = logging.getLogger()
    status = "All tesks(total(%d), actual(%d), actual_success(%d), actual_error(%d)) in file (%s) finished" % (len(
        run_jobs) + len(has_success_jobs), len(run_jobs), len(success_jobs), len(error_jobs), os.path.abspath(qjobs.jfile))
    if len(error_jobs) == 0:
        status += " successfully."
    else:
        status += ", but there are ERROR tesks."
    logger.info(status)

    qjobs.writestates(os.path.join(qjobs.logdir, "job.status.txt"))
    logger.info(str(dict(Counter([j.status for j in run_jobs]))))


@LogExc
def main():
    args = parseArgs()
    logger = Mylog(logfile=args.log, level="debug" if args.debug else "info")
    global clear, qjobs
    clear = args.noclean
    h = ParseSingal()
    h.start()
    qjobs = qsub(args.jobfile, args.num, args.injname,
                 args.start, args.end, mode=args.mode, usestrict=args.strict)
    qjobs.run(times=args.resub - 1, resubivs=args.resubivs)
    sumJobs(qjobs)


if __name__ == "__main__":
    main()
