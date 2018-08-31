# testsrunner

The testsrunner module provides a modular implementation of argument parsing interfaces.It provides an easy way to define user friendly command line interfaces. It uses cdp for parsing arguments.

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
To run tests with coverage, you will need to define the packages that you want to collect coverage info on. Define those packages in a json file as follows, and pass it to the test runner run_tests.py.
```
  $ cat coverage.json
  {
     "include": ["testsrunner"]
  }
  $ run_tests.py -v 2 -H -c coverage.json
```
If running tests from a repository, then coverage information should be collecting from packages in the repository:
```
  $ run_tests.py -v 2 -H -c coverage.json --coverage-from-repo
```
