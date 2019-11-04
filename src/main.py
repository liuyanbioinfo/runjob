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
        sumJobs(qjobs)
        if clear:
            call('qdel "*_%d"' % os.getpid(),
                 shell=True, stderr=PIPE, stdout=PIPE)
            pid = os.getpid()
            gid = os.getpgid(pid)
            call("kill -9 -%d" % gid, shell=True, stderr=PIPE, stdout=PIPE)
        sys.exit(signum)


def LogExc(f):
    @functools.wraps(f)
    def wrapper(*largs, **kwargs):
        try:
            res = f(*largs, **kwargs)
        except Exception, e:
            logging.get_logger(__name__).exception(e)
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
    parser.add_argument('-v', '--version',
                        action='version', version="%(prog)s v" + __version__)
    parser.add_argument('-i', '--injname', help="job names you need to run, default: all jobnames of you job file",
                        nargs="*", type=str, metavar="<str>")
    parser.add_argument('-s', '--start', help="job beginning with the number you given, 1 by default",
                        type=int, default=1, metavar="<int>")
    parser.add_argument('-e', '--end', help="job ending with the number you given, last job by default",
                        type=int, metavar="<int>")
    parser.add_argument('-r', '--resub', help="rebsub you job when error, 0 or minus means do not re-submit, 3 times by default",
                        type=int, default=3, metavar="<int>")
    parser.add_argument('-ivs', '--resubivs', help="rebsub interval seconds, 2 by default",
                        type=int, default=2, metavar="<int>")
    parser.add_argument("-m", '--mode', type=str, default="sge", choices=[
                        "sge", "localhost"], help="the mode to submit your jobs, 'sge' by default.")
    parser.add_argument("-nc", '--noclean', action="store_false", help="whether to clean all jobs or subprocess created by this programe when the main process exits, default: clean.",
                        default=True)
    return parser.parse_args()


def Mylog(logfile=None, level="info", name=None):
    logger = logging.getLogger(name)
    f = logging.Formatter(
        '[%(levelname)s %(processName)s %(asctime)s] %(message)s')
    if logfile is None:
        h = logging.StreamHandler(sys.stdout)  # default: sys.stderr
    else:
        h = logging.FileHandler(logfile, mode='w')
    h.setFormatter(f)
    logger.addHandler(h)
    if level.lower() == "info":
        logger.setLevel(logging.INFO)
    elif level.lower() == "debug":
        logger.setLevel(logging.DEBUG)
    return logger


def sumJobs(qjobs):
    thisrunjobs = set([j.name for j in qjobs.jobs])
    realrunjobs = thisrunjobs - qjobs.has_success
    realrunsuccess = qjobs.success - qjobs.has_success
    realrunerror = qjobs.error
    resubjobs = set(
        [k for k, v in qjobs.subtimes.items() if v != qjobs.times])
    thisjobstates = qjobs.state
    # qjobs.writejob(qjobs.jfile + ".bak")  ## write a new job file

    logger = logging.getLogger(__name__)
    if len(realrunerror) == 0:
        logger.info("All tesks(total(%d), actual(%d), actual_success(%d), actual_error(%d)) in file (%s) finished successfully.",
                    len(thisrunjobs), len(realrunjobs), len(realrunsuccess), len(realrunerror), os.path.abspath(qjobs.jfile))
    else:
        logger.info("All tesks( total(%d), actual(%d), actual_success(%d), actual_error(%d) ) in file (%s) finished, But there are ERROR tesks.",
                    len(thisrunjobs), len(realrunjobs), len(realrunsuccess), len(realrunerror), os.path.abspath(qjobs.jfile))

    qjobs.writestates(os.path.join(qjobs.logdir, "job.status.txt"))
    logger.info(str(dict(Counter(thisjobstates.values()))))


@LogExc
def main():
    args = parseArgs()
    mainlogger = Mylog(name=__name__)
    global clear, qjobs
    clear = args.noclean
    h = ParseSingal()
    h.start()
    qjobs = qsub(args.jobfile, args.num, args.injname,
                 args.start, args.end, mode=args.mode)
    statelogger = Mylog(logfile=os.path.join(
        qjobs.logdir, "job.run.txt"), name="state")
    qjobs.run(times=args.resub - 1, resubivs=args.resubivs)
    sumJobs(qjobs)


if __name__ == "__main__":
    main()
