import os
import sys
from testsrunner import TestRunnerBase


test_suite_name = 'testsrunner'

workdir = os.getcwd()

runner = TestRunnerBase(test_suite_name, test_data_files_info=os.path.join(os.path.dirname(__file__),"share", "test_data_files.txt"))
ret_code = runner.run(workdir)
sys.exit(ret_code)
