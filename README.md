# testsrunner

[![CircleCI](https://circleci.com/gh/CDAT/TestsRunner/tree/master.svg?style=svg)](https://circleci.com/gh/CDAT/TestsRunner/tree/master)
[![Coverage Status](https://coveralls.io/repos/github/CDAT/TestsRunner/badge.svg)](https://coveralls.io/github/CDAT/TestsRunner)

The testsrunner module provides a modular implementation of argument parsing interfaces. It provides an easy way to define user friendly command line interfaces. It uses cdp for parsing arguments.

# Example
Example on how to write a runner program run_tests.py for a project / test suite
using testsrunner:
```
  $ cat run_tests.py
  import os
  import sys
  from testsrunner import TestRunnerBase

  test_suite_name = 'testsrunner'
  workdir = os.getcwd()

  runner = TestRunnerBase(test_suite_name)
  ret_code = runner.run(workdir)
  sys.exit(ret_code)
```
### Run tests with coverage

To run tests with coverage, you will need to define the packages that you want to collect coverage info on. Define those packages in a json file as follows, and pass it to run_tests.py.
```
  $ cat coverage.json
  {
     "include": ["testsrunner"]
  }
```
To run tests with coverage, and collect coverage information from packages installed in the conda environment:
```
  $ run_tests.py -v 2 -H -c coverage.json
```
To run tests with coverage, and collect coverage information from packages / modules in the repository:

```
  $ run_tests.py -v 2 -H -c coverage.json --coverage-from-repo
```
If a test launches subprocesses, and coverage is to be collected on the subprocesses, then coverage.json file should list the subprocesses. Example:
```
$ cat coverage.json
{
   "include": ["testsrunner"],
   "subprocess": ["bin/print_something.py"]
}
```

### Run tests and checkout baseline from the same branch as your repository

```
  $ run_tests.py -v 2 -H --checkout-baseline --no-baselines-fallback-on-master
```

### Run tests and checkout baseline from 'master' branch if there is no baseline with same branch.

```
  $ run_tests.py -v 2 -H --checkout-baseline 
```

