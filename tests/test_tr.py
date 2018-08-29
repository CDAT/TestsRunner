import unittest
import os
import sys
import subprocess
import shlex

this_dir = os.path.abspath(os.path.dirname(__file__))
lib_dir = os.path.join(this_dir, '..', 'lib')
sys.path.append(lib_dir)

from testsrunner import TestRunnerBase


class TestRunnerBaseSubClass(TestRunnerBase):
    def __init__(self, test_suite_name, options=[], options_files=[],
                 get_sample_data=False,
                 test_data_files_info=None):
        super(TestRunnerBaseSubClass, self).__init__(test_suite_name,
                                                     options, options_files,
                                                     get_sample_data, test_data_files_info)


class TestTestRunnerBase(unittest.TestCase):
    
    def testRun(self):
        workdir = os.path.join(os.path.dirname ( __file__), os.path.pardir)
        print("xxxxxx workdir: {}".format(workdir))
        testsuite_name = "testsrunner"
        options_files = []
        options_files.insert(0, os.path.join(
                sys.prefix, "share", "testsrunner", "test_options_file.json"))
        
        runner = TestRunnerBaseSubClass(testsuite_name, options_files=options_files)
        print("xxxxxx calling runner.run() xxx")
        ret_code = runner.run(workdir, tests="tests/test_hello.py")
        self.assertEqual(ret_code, 0)

