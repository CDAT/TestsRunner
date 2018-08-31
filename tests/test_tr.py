import unittest
import os
import sys

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
        testsuite_name = "testsrunner"
        options_files = []
        option_file = os.path.join(this_dir, '..', 'resources', 'test_options_file.json')
        options_files.insert(0, option_file)
        options = [ "-s", "--with-coverage", "--cover-html", "--cover-xml", "--cover-package" ]
        runner = TestRunnerBaseSubClass(testsuite_name, options=options,
                                        options_files=options_files)
        ret_code = runner.run(workdir, tests="tests/test_tr_flake8.py")
        self.assertEqual(ret_code, 0)


