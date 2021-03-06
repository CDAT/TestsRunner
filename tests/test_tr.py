import unittest
import os
import shutil
import subprocess


from testsrunner import TestRunnerBase
from testsrunner.Util import run_command
this_dir = os.path.abspath(os.path.dirname(__file__))


class TestRunnerBaseSubClass(TestRunnerBase):
    def __init__(self, test_suite_name, options=[], options_files=[],
                 get_sample_data=False,
                 test_data_files_info=None):
        super(TestRunnerBaseSubClass, self).__init__(test_suite_name,
                                                     options, options_files,
                                                     get_sample_data,
                                                     test_data_files_info)


class TestTestRunnerBase(unittest.TestCase):

    def __get_git_branch(self, workdir):
        os.chdir(workdir)
        ret_code, cmd_output = run_command('git rev-parse --abbrev-ref HEAD')
        o = "".join(cmd_output)
        branch = o.strip()
        return(branch)

    def setUp(self):
        testsuite_name = "testsrunner"
        options_files = []
        option_file = os.path.join(this_dir, '..', 'tests',
                                   'test_options_file.json')
        options_files.insert(0, option_file)
        options = ["-s", "--with-coverage", "--cover-html", "--cover-xml",
                   "--cover-package", "--coverage"]
        test_data_files = os.path.join(this_dir, '..', 'tests',
                                       'test_data_files.txt')

        self.runner = TestRunnerBaseSubClass(testsuite_name, options=options,
                                             options_files=options_files,
                                             get_sample_data=True,
                                             test_data_files_info=test_data_files)

    def testRun(self):
        print("...testRun...")
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_passing_test.py")
        self.assertEqual(ret_code, 0)

    def testGenerateHtml(self):
        print("...testGenerateHtml...")
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_passing_test.py")
        self.assertEqual(ret_code, 0)
        print("....after run...")
        ret_code = self.runner._generate_html(workdir, open_browser=False)
        self.assertEqual(ret_code, 0)
        print("...leaving...testGenerateHtml...")

    def testPackageResults(self):
        print("...testPackageResults...")
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        ret_code = self.runner.run(workdir, tests="tests/test_passing_test.py")
        self.assertEqual(ret_code, 0)
        ret_code = self.runner._generate_html(workdir, open_browser=False)
        self.assertEqual(ret_code, 0)

        ret_code = self.runner._package_results(workdir)
        self.assertEqual(ret_code, 0)

    def testGetBaselines(self):
        print("...testGetBaselines...")
        workdir = os.path.join(os.path.dirname(__file__), os.path.pardir)
        data_dir = os.path.join(workdir, "uvcdat-testdata")
        if os.path.isdir(data_dir):
            shutil.rmtree(data_dir)
        branch = self.__get_git_branch(workdir)
        if branch != 'master':
            self.runner.no_baselines_fallback_on_master = True
            with self.assertRaises(Exception) as context:
                ret_code = self.runner._get_baseline(workdir)
            self.runner.no_baselines_fallback_on_master = False

        ret_code = self.runner._get_baseline(workdir)
        self.assertEqual(ret_code, 0)

    def testSubprocess(self):
        print("...testSubprocess...")
        subprocess.call(["print_something.py"])
        self.assertEqual(0, 0)
