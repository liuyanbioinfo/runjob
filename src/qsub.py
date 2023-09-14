#!/usr/bin/env python
# coding:utf-8

from . import dag
from .utils import *
from .job import Jobfile
from .run import RunJob
from .config import load_config


class qsub(RunJob):

    def __init__(self, config=None, **kwargs):
        '''
        all attribute of config or kwargs:
            @jobfile <file, list>: required
            @mode <str>: default: sge
            @queue <list>: default: all access queue
            @num <int>: default: total jobs
            @startline <int>: default: 1
            @endline <int>: default: None
            @strict <bool>: default: False
            @force <bool>: default: False
            @max_check <int>: default: 3
            @max_submit <int>: default: 30
            @loglevel <int>: default: None
            @quiet <bool>: default False
            @retry <int>: retry times, default: 0
            @retry_ivs <int>: retryivs sec, default: 2
            @sec <int>: submit epoch ivs, default: 2
        '''
        self.conf = config = config or load_config()
        for k, v in kwargs.items():
            setattr(self.conf.info.args, k, v)
        self.quiet = config.quiet
        self.jobfile = config.jobfile
        self.queue = config.queue
        self.maxjob = config.num
        self.strict = config.strict or False
        self.workdir = config.workdir or os.getcwd()
        self.jf = jf = Jobfile(self.jobfile, mode=config.mode or "sge")
        self.jfile = self.jf._path
        self.mode = jf.mode
        self.name = os.getpid()
        self.jobs = jf.jobs(
            config.injname, config.startline or 1, config.endline)
        self.logdir = jf.logdir
        self.retry = config.retry or 0
        self.retry_ivs = config.retry_ivs or 2
        self.sec = config.sec or 2
        self._init()
        self.lock = Lock()

    def _init(self):
        self.jobnames = [j.name for j in self.jobs]
        self.totaljobdict = {jf.name: jf for jf in self.jf.totaljobs}
        self.orders = self.jf.orders()
        self.is_run = False
        self.finished = False
        self.err_msg = ""
        self.reseted = False
        self.localprocess = {}
        self.cloudjob = {}
        self.jobsgraph = dag.DAG()
        self.has_success = []
        self.__create_graph()
        if self.conf.loglevel:
            self.logger.setLevel(self.conf.loglevel)
        self.check_rate = Fraction(
            self.conf.max_check or 3).limit_denominator()
        self.sub_rate = Fraction(
            self.conf.max_submit or 30).limit_denominator()
        self.sge_jobid = {}
        self.maxjob = self.maxjob or len(self.jobs)
        self.jobqueue = JobQueue(maxsize=min(max(self.maxjob, 1), 1000))

    def reset(self):
        self.jf = jf = Jobfile(self.jobfile, mode=self.mode)
        self.jobs = jf.jobs(
            self.conf.injname, self.conf.startline or 1, self.conf.endline)
        self._init()
        self.reseted = True

    def __create_graph(self):
        for k, v in self.orders.items():
            self.jobsgraph.add_node_if_not_exists(k)
            for i in v:
                self.jobsgraph.add_node_if_not_exists(i)
                self.jobsgraph.add_edge(i, k)
        for jn in self.jobsgraph.all_nodes.copy():
            if jn not in self.jobnames:
                self.jobsgraph.delete_node(jn)
        if len(self.jf.alljobnames) != len(set(self.jf.alljobnames)):
            names = [i for i, j in Counter(
                self.jf.alljobnames).items() if j > 1]
            self.throw("duplicate job name: %s" % " ".join(names))
        if self.jobsgraph.size() == 0:
            for jb in self.jobs:
                self.jobsgraph.add_node_if_not_exists(jb.name)

    def _qdel(self, name="", jobname=""):
        if name:
            call_cmd(['qdel', "*_%d" % os.getpid()])
            self.sge_jobid.clear()
        if jobname:
            jobid = self.sge_jobid.get(jobname, jobname)
            call_cmd(["qdel", jobid])
            if jobname in self.sge_jobid:
                self.sge_jobid.pop(jobname)


def main():
    parser = runjobArgparser()
    args = parser.parse_args()
    if args.jobfile.isatty():
        parser.print_help()
        return
    if args.jobfile is sys.stdin:
        jobfile = args.jobfile.readlines()
        args.jobfile.close()
        args.jobfile = jobfile
    else:
        args.jobfile.close()
        args.jobfile = args.jobfile.name
    if args.local:
        args.mode = "local"
    conf = load_config()
    conf.update_dict(**args.__dict__)
    logger = getlog(logfile=args.log, level=args.debug and "debug" or "info")
    qjobs = qsub(config=conf)
    try:
        qjobs.run()
    except (JobFailedError, QsubError) as e:
        if args.quiet:
            raise e
        sys.exit(10)
    except Exception as e:
        raise e


if __name__ == "__main__":
    sys.exit(main())
