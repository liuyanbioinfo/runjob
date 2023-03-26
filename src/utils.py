import os
import sys
import pdb
import psutil
import logging
import argparse
import threading

from collections import Counter
from subprocess import call, PIPE
from ratelimiter import RateLimiter
from functools import total_ordering

from .log import *
from ._version import __version__

if sys.version_info[0] < 3:
    from Queue import Queue
else:
    from queue import Queue


RUNSTAT = " && echo [`date +'%F %T'`] SUCCESS || echo [`date +'%F %T'`] ERROR"


class QsubError(Exception):
    pass


class JobRuleError(Exception):
    pass


class JobOrderError(Exception):
    pass


class myQueue(object):

    def __init__(self, maxsize=0):
        self._content = set()
        self._queue = Queue(maxsize=maxsize)
        self.sm = threading.Semaphore(maxsize)
        self.lock = threading.Lock()

    @property
    def length(self):
        return self._queue.qsize()

    def put(self, v, **kwargs):
        self._queue.put(v, **kwargs)
        # self.sm.acquire()
        if v not in self._content:
            with self.lock:
                self._content.add(v)

    def get(self, v=None):
        self._queue.get()
        # self.sm.release()
        if v is None:
            with self.lock:
                o = self._content.pop()
                return o
        else:
            if v in self._content:
                with self.lock:
                    self._content.remove(v)
                    return v

    @property
    def queue(self):
        return sorted(self._content)

    def isEmpty(self):
        return self._queue.empty()

    def isFull(self):
        return self._queue.full()


def Mylog(logfile=None, level="info", name=None):
    logger = logging.getLogger(name)
    if level.lower() == "info":
        logger.setLevel(logging.INFO)
    elif level.lower() == "debug":
        logger.setLevel(logging.DEBUG)
    if logfile is None:
        h = logging.StreamHandler()
    else:
        h = logging.FileHandler(logfile, mode='w')
    h.setFormatter(Formatter())
    logger.addHandler(h)
    return logger


def cleanAll(clear=False, qjobs=None, sumj=True):
    if qjobs is None:
        return
    stillrunjob = qjobs.jobqueue.queue
    if clear:
        pid = os.getpid()
        gid = os.getpgid(pid)
        for jn in stillrunjob:
            if jn.status in ["error", "success"]:
                continue
            jn.status = "killed"
            qjobs.logger.info("job %s status killed", jn.name)
        call_cmd(['qdel,  "*_%d"' % os.getpid()])
    else:
        for jn in stillrunjob:
            if jn.status in ["error", "success"]:
                continue
            jn.status += "-but-exit"
            qjobs.logger.info("job %s status %s", jn.name, jn.status)
    if sumj:
        sumJobs(qjobs)


def sumJobs(qjobs):
    run_jobs = qjobs.jobs
    has_success_jobs = qjobs.has_success
    error_jobs = [j for j in run_jobs if j.status == "error"]
    success_jobs = [j for j in run_jobs if j.status == 'success']

    logger = logging.getLogger()
    status = "All tesks(total(%d), actual(%d), actual_success(%d), actual_error(%d)) in file (%s) finished" % (len(
        run_jobs) + len(has_success_jobs), len(run_jobs), len(success_jobs), len(error_jobs), os.path.abspath(qjobs.jfile))
    SUCCESS = True
    if len(success_jobs) == len(run_jobs):
        status += " successfully."
    else:
        status += ", but there are Unsuccessful tesks."
        SUCCESS = False
    logger.info(status)
    qjobs.writestates(os.path.join(qjobs.logdir, "job.status.txt"))
    logger.info(str(dict(Counter([j.status for j in run_jobs]))))
    return SUCCESS


def style(string, mode='', fore='', back=''):
    STYLE = {
        'fore': Formatter.f_color_map,
        'back': Formatter.b_color_map,
        'mode': Formatter.mode_map,
        'default': {'end': 0},
    }
    mode = '%s' % STYLE["mode"].get(mode, "")
    fore = '%s' % STYLE['fore'].get(fore, "")
    back = '%s' % STYLE['back'].get(back, "")
    style = ';'.join([s for s in [mode, fore, back] if s])
    style = '\033[%sm' % style if style else ''
    end = '\033[%sm' % STYLE['default']['end'] if style else ''
    return '%s%s%s' % (style, string, end)


def get_job_state(state):
    s = state.lower() if state else state
    if s == 'running':
        return style(state, fore="cyan")
    if s == 'finished':
        return style(state, fore="green")
    elif s == 'waiting':
        return style(state, fore="white")
    elif s == 'failed':
        return style(state, fore="red")
    elif s == 'stopped':
        return style(state, fore="yellow")
    else:
        return style(state, fore="white")


def terminate_process(pid):
    try:
        pproc = psutil.Process(pid)
        for cproc in pproc.children(recursive=True):
            # cproc.terminate() # SIGTERM
            cproc.kill()  # SIGKILL
        # pproc.terminate()
        pproc.kill()
    except:
        pass


def call_cmd(cmd, verbose=False):
    shell = True
    if isinstance(cmd, list):
        shell = False
    if verbose:
        print(cmd)
        call(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
    else:
        with open(os.devnull, "w") as fo:
            call(cmd, shell=shell, stdout=fo, stderr=fo)


def runsgeArgparser():
    parser = argparse.ArgumentParser(
        description="For multi-run your shell scripts localhost, qsub or BatchCompute.")
    parser.add_argument("-wd", "--workdir", type=str, help="work dir, default: %s" %
                        os.path.abspath(os.getcwd()), default=os.path.abspath(os.getcwd()), metavar="<workdir>")
    parser.add_argument("-N", "--jobname", type=str,
                        help="job name", metavar="<jobname>")
    parser.add_argument("-lg", "--logdir", type=str,
                        help='the output log dir, default: "%s/runjob_*_log_dir"' % os.getcwd(), metavar="<logdir>")
    parser.add_argument("-n", "--num", type=int,
                        help="the max job number runing at the same time. default: all in your job file, max 1000", metavar="<int>")
    parser.add_argument("-s", "--startline", type=int,
                        help="which line number(1-base) be used for the first job tesk. default: 1", metavar="<int>", default=1)
    parser.add_argument("-e", "--endline", type=int,
                        help="which line number (include) be used for the last job tesk. default: all in your job file", metavar="<int>")
    parser.add_argument("-g", "--groups", type=int, default=1,
                        help="groups number of lines to a new jobs", metavar="<int>")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='log debug info', default=False)
    parser.add_argument("-l", "--log", type=str,
                        help='append log info to file, sys.stdout by default', metavar="<file>")
    parser.add_argument('-r', '--resub', help="rebsub you job when error, 0 or minus means do not re-submit, 0 by default",
                        type=int, default=0, metavar="<int>")
    parser.add_argument('--init', help="initial command before all task if set, will be running in localhost",
                        type=str,  metavar="<cmd>")
    parser.add_argument('--call-back', help="callback command if set, will be running in localhost",
                        type=str,  metavar="<cmd>")
    parser.add_argument('--mode', type=str, default="sge", choices=[
                        "sge", "local", "localhost", "batchcompute"], help="the mode to submit your jobs, 'sge' by default")
    parser.add_argument('-ivs', '--resubivs', help="rebsub interval seconds, 2 by default",
                        type=int, default=2, metavar="<int>")
    parser.add_argument('--rate', help="rate limite for job status checking per second, 3 by default",
                        type=int, default=3, metavar="<int>")
    parser.add_argument('-ini', '--ini',
                        help="input configfile for configurations search.", metavar="<configfile>")
    parser.add_argument("-config", '--config',   action='store_true',
                        help="show configurations and exit.",  default=False)
    parser.add_argument("-f", "--force", default=False, action="store_true",
                        help="force to submit jobs ingore already successed jobs, skip by default")
    parser.add_argument("--local", default=False, action="store_true",
                        help="submit your jobs in localhost, same as '--mode local'")
    parser.add_argument("--strict", action="store_true", default=False,
                        help="use strict to run. Means if any errors occur, clean all jobs and exit programe. off by default")
    parser.add_argument('-v', '--version',
                        action='version', version="v" + __version__)
    sge = parser.add_argument_group("sge arguments")
    sge.add_argument("-q", "--queue", type=str, help="the queue your job running, multi queue can be sepreated by whitespace, all access queue by default",
                     nargs="*", metavar="<queue>")
    sge.add_argument("-m", "--memory", type=int,
                     help="the memory used per command (GB), default: 1", default=1, metavar="<int>")
    sge.add_argument("-c", "--cpu", type=int,
                     help="the cpu numbers you job used, default: 1", default=1, metavar="<int>")
    batchcmp = parser.add_argument_group("batchcompute arguments")
    batchcmp.add_argument("-om", "--out-maping", type=str,
                          help='the oss output directory if your mode is "batchcompute", all output file will be mapping to you OSS://BUCKET-NAME. if not set, any output will be reserved', metavar="<dir>")
    batchcmp.add_argument('--access-key-id', type=str,
                          help="AccessKeyID while access oss", metavar="<str>")
    batchcmp.add_argument('--access-key-secret', type=str,
                          help="AccessKeySecret while access oss", metavar="<str>")
    batchcmp.add_argument('--regin', type=str, default="BEIJING", choices=['BEIJING', 'HANGZHOU', 'HUHEHAOTE', 'SHANGHAI',
                                                                           'ZHANGJIAKOU', 'CHENGDU', 'HONGKONG', 'QINGDAO', 'SHENZHEN'], help="batch compute regin, BEIJING by default")
    parser.add_argument("-j", "--jobfile", type=str,
                        help="the input jobfile", metavar="<jobfile>")
    return parser


def shellJobArgparser(arglist):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-q", "--queue", type=str, nargs="*")
    parser.add_argument("-m", "--memory", type=int)
    parser.add_argument("-c", "--cpu", type=int)
    parser.add_argument("-g", "--groups", type=int)
    parser.add_argument("-n", "--jobname", type=str)
    parser.add_argument("-om", "--out-maping", type=str)
    parser.add_argument("-wd", "--workdir", type=str)
    parser.add_argument('--mode', type=str)
    parser.add_argument("--local", default=False, action="store_true")
    return parser.parse_known_args(arglist)[0]
