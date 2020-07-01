import unittest
import os

from testsrunner import TestRunnerBase

this_dir = os.path.abspath(os.path.dirname(__file__))


class TestRunnerBaseSubClass(TestRunnerBase):
    def __init__(self, test_suite_name, options=[], options_files=[],
                 get_sample_data=False,
                 test_data_files_info=None):
        super(TestRunnerBaseSubClass, self).__init__(test_suite_name,
                                                     options, options_files,
                                                     get_sample_data, test_data_files_info)


class TestTestRunnerBase(unittest.TestCase):

    def setUp(self):
        testsuite_name = "testsrunner"
        options_files = []
        option_file = os.path.join(this_dir, '..', 'tests', 'test_options_file.json')
        options_files.insert(0, option_file)
        options = ["-s", "--timeout", "--coverage", "--coverage-from-egg"]
        options += ["--with-coverage", "--cover-html", "--cover-xml", "--cover-package", "--coverage"]
        self.runner = TestRunnerBaseSubClass(testsuite_name, options=options,
                                             options_files=options_files)

    def testRunPass(self):
        # Make sure it passes with default timeout (3660)
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_timeout.py")
        self.assertEqual(ret_code, 0)

    def testRunfail(self):
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        # Now set timeout to 2s to forece fail
        self.runner.args.timeout = 2
        ret_code = 1
        with self.assertRaises(Exception):
            ret_code = self.runner.run(workdir, tests="tests/test_timeout.py")
