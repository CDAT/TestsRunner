import unittest
import os
import sys

this_dir = os.path.abspath(os.path.dirname(__file__))
lib_dir = os.path.join(this_dir, '..', 'lib')
sys.path.append(lib_dir)

from testsrunner import TestRunnerBase
from Util import run_command

class TestRunnerBaseSubClass(TestRunnerBase):
    def __init__(self, test_suite_name, options=[], options_files=[],
                 get_sample_data=True,
                 test_data_files_info=None):
        super(TestRunnerBaseSubClass, self).__init__(test_suite_name,
                                                     options, options_files,
                                                     get_sample_data, test_data_files_info)

class TestTestRunnerBase(unittest.TestCase):

    def setUp(self):
        testsuite_name = "testsrunner"
        options_files = []
        option_file = os.path.join(this_dir, '..', 'resources', 'test_options_file.json')
        options_files.insert(0, option_file)
        options = [ "-s", "--with-coverage", "--cover-html", "--cover-xml", "--cover-package", "--coverage" ]
        self.runner = TestRunnerBaseSubClass(testsuite_name, options=options,
                                             options_files=options_files)

    def testRun(self):
        workdir = os.path.join(os.path.dirname ( __file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_tr_flake8.py")
        self.assertEqual(ret_code, 0)

    def testGetBaseline(self):
        workdir = os.path.join(os.path.dirname ( __file__), os.path.pardir)
        ret_code = self.runner._get_baseline(workdir)
        self.assertEqual(ret_code, 0)

    def testGenerateHtml(self):
        workdir = os.path.join(os.path.dirname ( __file__), os.path.pardir)
        self.runner.run(workdir, tests="tests/test_tr_flake8.py")
        ret_code = self.runner._generate_html(workdir)
        self.assertEqual(ret_code, 0)

    def testPackageResults(self):
        workdir = os.path.join(os.path.dirname ( __file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_tr_flake8.py")
        ret_code = self.runner._package_results(workdir)
        self.assertEqual(ret_code, 0)




