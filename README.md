# runjob

[![OSCS Status](https://www.oscs1024.com/platform/badge/yodeng/runjob.svg?size=small)](https://www.oscs1024.com/project/yodeng/runjob?ref=badge_small)
[![PyPI version](https://img.shields.io/pypi/v/runjob.svg?logo=pypi&logoColor=FFE873)](https://pypi.python.org/pypi/runjob)
[![Downloads](https://static.pepy.tech/badge/runjob)](https://pepy.tech/project/runjob)
[![install with bioconda](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat)](https://anaconda.org/bioconda/runjob)

## Summary

runjob is a program for managing a group of related jobs running on a compute cluster `localhost`, [Sun Grid Engine](http://star.mit.edu/cluster/docs/0.93.3/guides/sge.html), [BatchCompute](https://help.aliyun.com/product/27992.html) .  It provides a convenient method for specifying dependencies between jobs and the resource requirements for each job (e.g. memory, CPU cores). It monitors the status of the jobs so you can tell when the whole group is done. Litter cpu or memory resource is used in the login compute node.

## OSCS

[![OSCS Status](https://www.oscs1024.com/platform/badge/yodeng/runjob.svg?size=large)](https://www.oscs1024.com/project/yodeng/runjob?ref=badge_large)

## Software Requirements

python >=3.5

## Installation

The development version can be installed with (for recommend)

```
pip install git+https://github.com/yodeng/runjob.git
```

The stable release (maybe not latest) can be installed with

> pypi:

```
pip install runjob -U
```

> conda:

```
conda install -c bioconda runjob
```

## User Guide

All manual can be found [here](https://runjob.readthedocs.io/en/latest/).

## Usage

You can get the quick help like this:

##### runjob/runflow：

	$ runjob --help 
	Usage: runjob [-h] [-v] [-j [<jobfile>]] [-n <int>] [-s <int>] [-e <int>] [-w <workdir>] [-d] [-l <file>] [-r <int>] [-R <int>] [-f] [--dag] [--dag-extend] [--mode {sge,local,localhost,batchcompute}]
	              [--local] [--strict] [--quiet] [--ini <configfile>] [--config] [--max-check <float>] [--max-submit <float>] [--max-queue-time <float/str>] [--max-run-time <float/str>]
	              [--max-wait-time <float/str>] [--max-timeout-retry <int>] [-i [<str> ...]] [-L <logdir>]
	
	runjob is a tool for managing parallel tasks from a specific job file running in localhost or sge cluster.
	
	Optional Arguments:
	  -h, --help            show this help message and exit
	  -i, --injname [<str> ...]
	                        job names you need to run. (default: all job names of the jobfile)
	  -L, --logdir <logdir>
	                        the output log dir. (default: join(dirname(jobfile), "logs"))
	
	Base Arguments:
	  -v, --version         show program's version number and exit
	  -j, --jobfile [<jobfile>]
	                        input jobfile, if empty, stdin is used. (required)
	  -n, --num <int>       the max job number runing at the same time. (default: all of the jobfile, max 1000)
	  -s, --start <int>     which line number(1-base) be used for the first job. (default: 1)
	  -e, --end <int>       which line number (include) be used for the last job. (default: last line of the jobfile)
	  -w, --workdir <workdir>
	                        work directory. (default: /share/data3/dengyong/soft/runjob)
	  -d, --debug           log debug info.
	  -l, --log <file>      append log info to file. (default: stdout)
	  -r, --retry <int>     retry N times of the error job, 0 or minus means do not re-submit. (default: 0)
	  -R, --retry-sec <int>
	                        retry the error job after N seconds. (default: 2)
	  -f, --force           force to submit jobs even if already successed.
	  --dag                 do not execute anything and print the directed acyclic graph of jobs in the dot language.
	  --dag-extend          do not execute anything and print the extend directed acyclic graph of jobs in the dot language.
	  --mode {sge,local,localhost,batchcompute}
	                        the mode to submit your jobs, if no sge installed, always localhost. (default: sge)
	  --local               submit your jobs in localhost, same as '--mode local'.
	  --strict              use strict to run, means if any errors, clean all jobs and exit.
	  --quiet               suppress all output and logging.
	  --ini <configfile>    input configfile for configurations search.
	  --config              show configurations and exit.
	  --max-check <float>   maximal number of job status checks per second, fractions allowed. (default: 3)
	  --max-submit <float>  maximal number of jobs submited per second, fractions allowed. (default: 30)
	
	Time Control Arguments:
	  --max-queue-time <float/str>
	                        maximal time (d/h/m/s) between submit and running per job. (default: no-limiting)
	  --max-run-time <float/str>
	                        maximal time (d/h/m/s) start from running per job. (default: no-limiting)
	  --max-wait-time <float/str>
	                        maximal time (d/h/m/s) start from submit per job. (default: no-limiting)
	  --max-timeout-retry <int>
	                        retry N times for the timeout error job, 0 or minus means do not re-submit. (default: 0)

##### runsge/runshell/runbatch:

```
$ runsge --help 
Usage: runsge [-h] [-v] [-j [<jobfile>]] [-n <int>] [-s <int>] [-e <int>] [-w <workdir>] [-d] [-l <file>] [-r <int>] [-R <int>] [-f] [--dot] [--dot-shrinked] [--mode {sge,local,localhost,batchcompute}]
              [--local] [--strict] [--quiet] [--ini <configfile>] [--config] [--max-check <float>] [--max-submit <float>] [--max-queue-time <float/str>] [--max-run-time <float/str>]
              [--max-wait-time <float/str>] [--max-timeout-retry <int>] [-N <jobname>] [-L <logdir>] [-g <int>] [--init <cmd>] [--call-back <cmd>] [-q [<queue> ...]] [-m <int>] [-c <int>] [--out-maping <dir>]
              [--access-key-id <str>] [--access-key-secret <str>] [--region {beijing,hangzhou,huhehaote,shanghai,zhangjiakou,chengdu,hongkong,qingdao,shenzhen}]

runsge is a tool for managing parallel tasks from a specific shell scripts runing in localhost, sge or batchcompute.

Optional Arguments:
  -h, --help            show this help message and exit
  -N, --jobname <jobname>
                        job name. (default: basename of the jobfile)
  -L, --logdir <logdir>
                        the output log dir. (default: "/share/data3/dengyong/soft/runjob/runsge_*_log_dir")
  -g, --groups <int>    N lines to consume a new job group. (default: 1)
  --init <cmd>          command before all jobs, will be running in localhost.
  --call-back <cmd>     command after all jobs finished, will be running in localhost.

Base Arguments:
  -v, --version         show program's version number and exit
  -j, --jobfile [<jobfile>]
                        input jobfile, if empty, stdin is used. (required)
  -n, --num <int>       the max job number runing at the same time. (default: all of the jobfile, max 1000)
  -s, --start <int>     which line number(1-base) be used for the first job. (default: 1)
  -e, --end <int>       which line number (include) be used for the last job. (default: last line of the jobfile)
  -w, --workdir <workdir>
                        work directory. (default: /share/data3/dengyong/soft/runjob)
  -d, --debug           log debug info.
  -l, --log <file>      append log info to file. (default: stdout)
  -r, --retry <int>     retry N times of the error job, 0 or minus means do not re-submit. (default: 0)
  -R, --retry-sec <int>
                        retry the error job after N seconds. (default: 2)
  -f, --force           force to submit jobs even if already successed.
  --dot                 do not execute anything and print the directed acyclic graph of jobs in the dot language.
  --dot-shrinked        do not execute anything and print the shrinked directed acyclic graph of jobs in the dot language.
  --mode {sge,local,localhost,batchcompute}
                        the mode to submit your jobs, if no sge installed, always localhost. (default: sge)
  --local               submit your jobs in localhost, same as '--mode local'.
  --strict              use strict to run, means if any errors, clean all jobs and exit.
  --quiet               suppress all output and logging.
  --ini <configfile>    input configfile for configurations search.
  --config              show configurations and exit.
  --max-check <float>   maximal number of job status checks per second, fractions allowed. (default: 3)
  --max-submit <float>  maximal number of jobs submited per second, fractions allowed. (default: 30)

Time Control Arguments:
  --max-queue-time <float/str>
                        maximal time (d/h/m/s) between submit and running per job. (default: no-limiting)
  --max-run-time <float/str>
                        maximal time (d/h/m/s) start from running per job. (default: no-limiting)
  --max-wait-time <float/str>
                        maximal time (d/h/m/s) start from submit per job. (default: no-limiting)
  --max-timeout-retry <int>
                        retry N times for the timeout error job, 0 or minus means do not re-submit. (default: 0)

Sge Arguments:
  -q, --queue [<queue> ...]
                        the queue your job running, multi queue can be sepreated by whitespace. (default: all accessed queue)
  -m, --memory <int>    the memory used per command (GB). (default: 1)
  -c, --cpu <int>       the cpu numbers you job used. (default: 1)

Batchcompute Arguments:
  --out-maping <dir>    the oss output directory if your mode is "batchcompute", all output file will be mapping to you OSS://BUCKET-NAME. if not set, any output will be reserved.
  --access-key-id <str>
                        AccessKeyID while access oss.
  --access-key-secret <str>
                        AccessKeySecret while access oss.
  --region {beijing,hangzhou,huhehaote,shanghai,zhangjiakou,chengdu,hongkong,qingdao,shenzhen}
                        batch compute region. (default: beijing)
```

##### qs/qcs:

```
$ qs --help 
For summary all jobs
Usage: qs [jobfile|logdir|logfile]
       qcs --help
```



## License

runjob is distributed under the [MIT license](./LICENSE).

## Contact

Please send comments, suggestions, bug reports and bug fixes to
yodeng@tju.edu.cn.

## Example

```
$ cat test.flow

logs: ./logs
envs:
    samples: A B C

qc:
    echo "qc $samples"
bwa:
    echo "bwa $samples"
    depends: qc.samples   ## each sample-bwa depends each sample-qc
    # depends: qc   ## each sample-bwa depends all sample-qc
sort:
    echo "sort $samples"
    depends: bwa.samples
index:
    echo "index $samples"
    depends: sort.samples
calling:
    echo "calling allsample"
    depends: index
stats:
    echo "stats allsample"
    depends: calling
```

command `runflow -j test.flow --dot | dot -Tsvg > test.svg` will get the job graph:

![test](https://github.com/yodeng/runjob/assets/18365846/4f628b3e-4216-47c1-9287-9525639a9e9b)

## Todo

More functions will be improved in the future.
