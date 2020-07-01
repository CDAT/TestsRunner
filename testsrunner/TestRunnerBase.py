from __future__ import print_function
from functools import partial
import glob
import sys
import os
import multiprocessing
import codecs
import time
import webbrowser
import json
import cdp
from .Util import run_command, download_sample_data_files
from .Util import get_sampledata_path, run_nose
from .image_compare import script_data
import tempfile
from subprocess import Popen, PIPE
import shlex
import pkg_resources
SUCCESS = 0
FAILURE = 1
egg_path = pkg_resources.resource_filename(pkg_resources.Requirement.parse("testsrunner"), "share/testsrunner")


multiprocessing.freeze_support()
multiprocessing.set_start_method('fork')

def _get_module_path(name):
    f = tempfile.NamedTemporaryFile(mode="w")
    print("from __future__ import print_function\nimport imp\n"
          "import {pkg}\nprint(imp.reload({pkg}).__path__[0])".format(
              pkg=name), file=f)
    f.file.flush()
    p = Popen(shlex.split("python {}".format(f.name)), stdout=PIPE,
              stderr=PIPE, cwd=tempfile.gettempdir())
    o, e = p.communicate()
    pkg = o.decode("utf-8").strip()
    return pkg


def _get_local_py_files(pkg):
    length = len(pkg) + 1
    local_py_files = []
    for path, subdirs, files in os.walk(pkg):
        for name in files:
            if name[-3:].lower() == ".py":
                local_py_files.append(os.path.join(path[length:], name))
    return local_py_files


class TestRunnerBase(object):

    """
    This is a base class for a test runner.
    Each test project's run_tests.py should instantiate this TestRunnerBase
    class, and call the run() method. For example:

      runner = TestRunnerBase.TestRunnerBase(test_suite_name, valid_options,
      args, get_sample_data)
      runner.run(workdir, args.tests)
    """
    def __init__(self, test_suite_name, options=[], options_files=[],
                 get_sample_data=False, test_data_files_info=None):
        """
           test_suite_name: test suite name
           options        : options to use (in addition of default options
                            always here)
           options_files  : json files defining cdp/addparse argument
                            definitions
           get_sample_data: specifies whether sample data should be downloaded
                            for the test run.
           test_data_files_info: file name of a text file containing list of
                            data files needed for the test suite.
        """
        #
        # workaround for https://github.com/pyinstaller/pyinstaller/issues/4865
        # running into this recursive loop with py3.8 macos
        #
        # multiprocessing.freeze_support()
        # multiprocessing.set_start_method('fork')

        options_files.insert(0, os.path.join(
            egg_path, "testsrunner.json"))
        # Remove possible duplicates
        options_files_used = []
        for filename in options_files:
            if filename not in options_files_used:
                options_files_used.append(filename)

        parser = cdp.cdp_parser.CDPParser(None, options_files_used)
        parser.add_argument("tests", nargs="*", help="Tests to run")
        options += ["--coverage", "--verbosity", "--num_workers",
                    "--attributes", "--parameters", "--diags",
                    "--baseline", "--checkout-baseline",
                    "--html", "--failed", "--package",
                    "--timeout",
                    "--coverage-from-repo", "--coverage-from-egg",
                    "--no-baselines-fallback-on-master"]
        for option in set(options):
            parser.use(option)

        self.args = parser.get_parameter()
        self.test_suite_name = test_suite_name
        self.verbosity = self.args.verbosity
        self.ncpus = self.args.num_workers
        self.no_baselines_fallback_on_master = \
            self.args.no_baselines_fallback_on_master
        self.restore_from = None

        if get_sample_data is True:
            if test_data_files_info is None:
                test_data_files_info = os.path.join(
                    "share", "test_data_files.txt")
            download_sample_data_files(test_data_files_info,
                                       get_sampledata_path())

    def _get_tests(self, workdir, tests=None):
        """
        get_tests() gets the list of test names to run.
        If <failed_only> is False, returns the set of the specified
        test names. If <tests> is not specified, returns a set of all tests
        under 'tests' sub directory.
        If <failed_only> is True, returns the set of failed test names
        from previous run.
        If <failed_only> is True, and <tests> is specified, returns
        the set of failed test names that is listed in <tests>
        """
        if tests is None or len(tests) == 0:
            test_names = glob.glob("{w}/tests/test_*py".format(w=workdir))
        else:
            test_names = set(tests)

        if self.args.failed and os.path.exists(os.path.join("tests",
                                                            ".last_failure")):
            f = open(os.path.join("tests", ".last_failure"))
            failed = set(eval(f.read().strip()))
            f.close()
            new_tests = []
            for failed_test in failed:
                if failed_test in test_names:
                    new_tests.append(failed_test)
            test_names = new_tests

        return test_names

    def _get_baseline(self, workdir):
        """
        _get_baseline(self, workdir):
        <workdir> : should be repo dir of the test
        """
        os.chdir(workdir)
        ret_code, cmd_output = self.__run_cmd(
            'git rev-parse --abbrev-ref HEAD')
        o = "".join(cmd_output)
        branch = o.strip()
        repo = os.path.basename(self.args.baseline)
        if not os.path.exists(repo):
            cmd = "git clone {}".format(self.args.baseline)
            ret_code, cmd_output = self.__run_cmd(cmd)
            if ret_code != SUCCESS:
                return ret_code
        os.chdir(repo)
        ret_code, cmd_output = self.__run_cmd("git pull")
        if ret_code != SUCCESS:
            return ret_code
        if self.verbosity > 1:
            print("BRANCH WE ARE TRYING TO CHECKOUT is (%s)" % branch)
        ret_code, cmd_output = self.__run_cmd("git checkout %s" % (branch))
        if ret_code != 0:
            if self.no_baselines_fallback_on_master:
                os.chdir(workdir)
                msg = "baseline does not exist for branch {}".format(branch)
                raise Exception(msg)
            else:
                print("Could not checkout branch `{}`, fallback on `master`".format(branch))
                ret_code, cmd_output = self.__run_cmd("git checkout master")
        os.chdir(workdir)
        return(ret_code)

    def __run_cmd(self, cmd):
        ret_code, cmd_output = run_command(cmd, True, self.verbosity)
        return ret_code, cmd_output

    def _prep_nose_options(self):
        """Place holder extend this if you want more options"""
        return []

    def __get_site_packages_path(self):
        python_ver = "python{a}.{i}".format(a=sys.version_info.major,
                                            i=sys.version_info.minor)
        path = os.path.join(sys.prefix, 'lib', python_ver, 'site-packages')
        return path

    def __get_coverage_packages_opt(self, workdir):
        with open(self.args.coverage, 'r') as f:
            coverage_info = json.load(f)

        coverage_opts = ""
        self.egg_paths = {}
        for pkg in coverage_info["include"]:
            path = _get_module_path(pkg)
            self.egg_paths[pkg] = path
            if not self.args.coverage_from_egg:
                opt = "--cover-package {p}".format(p=path)
                coverage_opts += " {new}".format(new=opt)
                if self.args.coverage_from_repo:
                    path = os.path.join(os.getcwd())
                    opt = "--cover-package {p}".format(
                        p=os.path.join(path, pkg))
                    coverage_opts += " {new}".format(new=opt)
        return coverage_opts.split()

    def __create_coverage_rc(self, workdir):
        '''
        This method is called when we need to get coverage on subprocesses.
        It creates a .coveragerc under <workdir>.
        It copies the content of a template file (coveragerc) to .coveragerc,
        and add any subprocesses to take coverage on under
        the 'include' entry in .coveragerc.
        The subprocesses are listed under 'subprocess' key in the file
        specified to the --coverage option.
        '''
        with open(self.args.coverage, 'r') as f:
            coverage_info = json.load(f)

        testsrunner_dir = egg_path
        template_file = os.path.join(testsrunner_dir, "coveragerc")
        coverage_rc = os.path.join(workdir, ".coveragerc")
        cmd = "cp {s} {d}".format(s=template_file, d=coverage_rc)
        ret_code, cmd_output = self.__run_cmd(cmd)
        if ret_code != SUCCESS:
            return ret_code
        try:
            with open(coverage_rc, "a+") as f:
                f.write("source =\n")
                for pkg in coverage_info["include"]:
                    local_files = _get_local_py_files(pkg)
                    egg = _get_module_path(pkg)
                    for name in local_files:
                        f.write("\t{}/{}\n".format(egg, name))
                        f.write("\t{}/{}\n".format(sys.prefix, name))
                if "subprocess" in coverage_info:
                    for a_subprocess in coverage_info["subprocess"]:
                        subprocess_file = os.path.join(sys.prefix,
                                                       a_subprocess)
                        f.write("\t{the_file}\n".format(
                            the_file=subprocess_file))
                if "scripts" in coverage_info:
                    for a_script in coverage_info["scripts"]:
                        f.write("\t{the_script}\n".format(the_script=a_script))
        except IOError:
            print("Could not create {}".format(coverage_rc))
            return FAILURE

        return SUCCESS, coverage_rc

    def __create_coverage_sitecustomize(self, workdir, rc_file):
        '''
        This method is called when we need to get coverage on subprocesses.
        It creates a 'sitecustomize.py' file under the python path which does:
        - sets the environment variable COVERAGE_PROCESS_START to the
          .coveragerc created by __create_coverage_rc() method,
        - invokes coverage.process_startup().
        NOTE: coverage.py examines COVERAGE_PROCESS_START environment
        variable. If it is set, coverage.py will invoke sitecustomize.py
        which forces python to run coverage.py on the subprocesses.
        '''
        path = self.__get_site_packages_path()
        self.sitecustomize_py = os.path.join(path, 'sitecustomize.py')
        if os.path.exists(self.sitecustomize_py):
            # need to save away and restore later.
            current_time = time.localtime(time.time())
            time_str = time.strftime(".%b.%d.%Y.%H:%M:%S", current_time)
            backup = os.path.join(path, 'sitecustomize.py' + time_str)
            cmd = "mv {source} {dest}".format(source=self.sitecustomize_py,
                                              dest=backup)
            self.restore_from = backup
            self.restore_to = self.sitecustomize_py
            ret_code, cmd_output = self.__run_cmd(cmd)
            if ret_code != SUCCESS:
                return ret_code
        try:
            with open(self.sitecustomize_py, "w+") as f:
                f.write("import coverage\n")
                f.write("import os\n")
                env = "COVERAGE_PROCESS_START"
                f.write("os.environ[\"{e}\"] = \"{v}\"\n".format(e=env,
                                                                 v=rc_file))
                f.write("coverage.process_startup()")
        except IOError:
            print("Could not create {}".format(self.sitecustomize_py))
            return FAILURE
        return SUCCESS

    def __do_setup_if_coverage_subprocesses(self, workdir):
        '''
        This method is called when coverage is to be done on
        subprocesses, which is indicated by the presence of
        "subprocess" entry in the file specified with
        --coverage option.
        '''
        ret_code = SUCCESS
        with open(self.args.coverage, 'r') as f:
            coverage_info = json.load(f)

        if "subprocess" in coverage_info or "scripts" in coverage_info:
            ret_code, rc_file = self.__create_coverage_rc(workdir)
            if ret_code != SUCCESS:
                return ret_code
            ret_code = self.__create_coverage_sitecustomize(workdir, rc_file)

        return ret_code

    def __collect_coverage(self, workdir):
        coverage_files = glob.glob(".cvrg/*")
        coverage_files += glob.glob(".cvrg.*")
        if os.path.exists(".coveragerc"):
            with open(".coveragerc") as f:
                lines = f.readlines()
            with open(".coveragerc", "w") as f:
                for ln in lines:
                    if "data_file" not in ln:
                        print(ln, file=f)
        print("COV FILES:", coverage_files)
        # replace moduyle path with repo path
        if self.args.coverage_from_egg:
            for filename in coverage_files:
                with open(filename) as f:
                    content = f.read()
                for pkg in self.egg_paths:
                    path = self.egg_paths[pkg]
                    if path.strip() != "":
                        content = content.replace(path,
                                                  os.path.join(os.getcwd(),
                                                               pkg))
                with open(filename, "w") as f:
                    f.write(content)
        run_command("coverage combine {}".format(" ".join(coverage_files)))
        run_command("coverage xml")
        run_command("coverage html")
        cmd = "coverage report -m"
        run_command(cmd, True, 2, 1)

    def __restore(self):
        # for coverage of subprocesses
        if self.restore_from:
            cmd = "mv {s} {d}".format(s=self.restore_from,
                                      d=self.restore_to)
            ret_code, cmd_output = self.__run_cmd(cmd)
            if ret_code != SUCCESS:
                return ret_code
            self.restore_from = None
        else:
            if hasattr(self, "sitecustomize_py") and \
                    os.path.exists(self.sitecustomize_py):
                os.remove(self.sitecustomize_py)

        return SUCCESS

    def _do_run_tests(self, workdir, test_names):
        ret_code = SUCCESS
        #
        # workaround for https://github.com/pyinstaller/pyinstaller/issues/4865
        # running into this recursive loop with py3.8 macos
        #
        # multiprocessing.freeze_support()
        # multiprocessing.set_start_method('fork')
        p = multiprocessing.Pool(self.ncpus)
        # Let's prep the options once and for all
        opts = self._prep_nose_options()
        if self.args.coverage:
            coverage_opts = self.__get_coverage_packages_opt(workdir)
            opts += ["--with-coverage", ]
            opts += coverage_opts
            if not os.path.exists(".cvrg"):
                os.makedirs(".cvrg")

            ret_code = self.__do_setup_if_coverage_subprocesses(workdir)
            if ret_code != SUCCESS:
                return ret_code
        for att in self.args.attributes:
            opts += ["-A", att]
        func = partial(run_nose, opts, self.verbosity)
        try:
            outs = p.map_async(func, test_names).get(self.args.timeout)
        except KeyboardInterrupt:
            sys.exit(1)
        results = {}
        failed = []
        for d in outs:
            results.update(d)
            test_name = list(d.keys())[0]
            if d[test_name]["result"] != 0:
                failed.append(test_name)
        try:
            os.makedirs("tests")
        except Exception:
            pass
        f = open(os.path.join("tests", ".last_failure"), "w")
        f.write(repr(failed))
        f.close()

        if self.verbosity > 0:
            if len(outs) > 0:
                print("Ran %i tests, %i failed (%.2f%% success)" % (len(outs), len(failed), 100. - float(len(failed)) / len(outs) * 100.))
            else:
                print("No test run")
            if len(failed) > 0:
                print("Failed tests:")
                for f in failed:
                    print("\t", f)

        self.results = results
        if len(failed) > 0:
            ret_code = FAILURE

        if self.args.coverage:
            self.__collect_coverage(workdir)
            self.__restore()
        return ret_code

    def __abspath(self, path, name, prefix):
        import shutil
        full_path = os.path.abspath(os.path.join(os.getcwd(), "..", path))
        if not os.path.exists(name):
            os.makedirs(name)
        new_path = os.path.join(name, prefix + "_" + os.path.basename(full_path))
        try:
            shutil.copy(full_path, new_path)
        except Exception:
            pass
        return new_path

    def __findDiffFiles(self, log):
        i = -1
        file1 = ""
        file2 = ""
        diff = ""
        N = len(log)
        while log[i].find("Source file") == -1 and i > -N:
            i -= 1
        if i > -N:
            file1 = log[i - 1].split()[-1]
            for j in range(i, N):
                if log[j].find("New best!") > -1:
                    if log[j].find("Comparing") > -1:
                        file2 = log[j].split()[2]
                    else:
                        k = j - 1
                        while log[k].find("Comparing") == -1 and k > -N:
                            k -= 1
                        try:
                            file2 = log[k].split()[2]
                        except Exception:
                            file2 = log[k].split()[1][:-1] + log[j].split()[0]
                            print("+++++++++++++++++++++++++", file2)
                if log[j].find("Saving image diff") > -1:
                    diff = log[j].split()[-1]
                    # break
        return file1, file2, diff

    def __write_html_header(self, fh):
        print("<!DOCTYPE html>", file=fh)
        html_str = '<html><head>' + \
            '<title>%s Test Results %s</title>' + \
            '<link rel="stylesheet" type="text/css"' + \
            'href="' + \
            'http://cdn.datatables.net/1.10.13/css/jquery.dataTables.css">' +\
            '<script type="text/javascript"' + \
            ' src="http://code.jquery.com/jquery-1.12.4.js"></script>' + \
            '<script type="text/javascript" charset="utf8" ' + \
            'src="https://' + \
            'cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js' + \
            '">' + \
            '</script>' + \
            '<script>' + \
            '$(document).ready( function () {' + \
            " $('#table_id').DataTable({" + \
            " \"order\":[[1,'asc'],[0,'asc']]," + \
            ' "scrollY":"70vh","paging":false,"scrollCollapse":false' + \
            '  });' + \
            ' } );' + \
            '</script>' + \
            '</head>'
        print(html_str % (self.test_suite_name, time.asctime()), file=fh)
        print("<body><h1>%s Test results: %s</h1>" % (self.test_suite_name,
                                                      time.asctime()), file=fh)
        print("<table id='table_id' class='display'>", file=fh)
        print("<thead><tr><th>Test</th><th>Result</th><th>Start Time</th>"
              "<th>End Time</th><th>Time</th></tr></thead>", file=fh)
        print("<tfoot><tr><th>Test</th><th>Result</th><th>Start Time</th>"
              "<th>End Time</th><th>Time</th></tr></tfoot>", file=fh)

    def _generate_html(self, workdir, image_difference=True,
                       open_browser=True):
        os.chdir(workdir)
        if not os.path.exists("tests_html"):
            os.makedirs("tests_html")
        os.chdir("tests_html")

        if image_difference:
            js = script_data()

        fi = open("index.html", "w")
        failed_fi = open("failed_index.html", "w")
        self.__write_html_header(fi)
        self.__write_html_header(failed_fi)

        any_failure = False
        for ts in sorted(self.results.keys()):
            result = self.results[ts]
            nm = ts.split("/")[-1][:-3]
            print("<tr><td>%s</td>" % nm, end=' ', file=fi)
            fe = codecs.open("%s.html" % nm, "w", encoding="utf-8")
            print("<!DOCTYPE html>", file=fe)
            print("<html><head><title>%s</title>" % nm, file=fe)
            if result["result"] == 0:
                print("<td><a href='%s.html'>OK</a></td>" % nm, end=' ',
                      file=fi)
                print("</head><body>", file=fe)
                print("<a href='index.html'>Back To Results List</a>", file=fe)
            else:
                any_failure = True
                print("<td><a href='%s.html'>Fail</a></td>" % nm,
                      end=' ', file=fi)
                print("<tr><td>%s</td>" % nm, end=' ', file=failed_fi)
                print("<td><a href='%s.html'>Fail</a></td>" % nm,
                      end=' ', file=failed_fi)
                print("<script type='text/javascript'>%s</script></head><body>"
                      % js, file=fe)
                print("<a href='index.html'>Back To Results List</a>", file=fe)
                print("<h1>Failed test: %s on %s</h1>" % (nm, time.asctime()),
                      file=fe)
                file1, file2, diff = self.__findDiffFiles(result["log"])
                if file1 != "":
                    print('<div id="comparison"></div><script'
                          ' type="text/javascript">'
                          ' ImageCompare.compare('
                          'document.getElementById("comparison"),'
                          ' "%s", "%s"); </script>' % (
                              self.__abspath(file2, nm, "test"),
                              self.__abspath(file1, nm, "source")), file=fe)
                    print("<div><a href='index.html'>"
                          "Back To Results List</a></div>",
                          file=fe)
                    print("<div id='diff'>"
                          "<img src='%s' alt='diff file'></div>" %
                          self.__abspath(diff, nm, "diff"), file=fe)
                    print("<div><a href='index.html'>Back To"
                          " Results List</a></div>", file=fe)
            print('<div id="output"><h1>Log</h1><pre>'
                  '%s</pre></div>' % "\n".join(result["log"]), file=fe)
            print("<a href='index.html'>Back To Results List</a>", file=fe)
            print("</body></html>", file=fe)
            fe.close()
            t = result["times"]
            end = t["end"]
            start = t["start"]
            print("<td>%s</td><td>%s</td><td>%s</td></tr>" % (time.ctime(start), time.ctime(end), end - start), file=fi)
            if result["result"]:
                print("<td>%s</td><td>%s</td><td>%s</td></tr>" % (time.ctime(start),
                                                                  time.ctime(end), end - start), file=failed_fi)
        print("</table></body></html>", file=fi)
        print("</table></body></html>", file=failed_fi)
        fi.close()
        failed_fi.close()
        if any_failure is False:
            os.unlink("failed_index.html")
        os.chdir(workdir)
        index_file = "{}/tests_html/index.html".format(workdir)
        if os.path.isfile(index_file):
            ret_code = SUCCESS
            if open_browser:
                webbrowser.open("file://%s" % index_file)
        else:
            ret_code = FAILURE
        return ret_code

    def _package_results(self, workdir):
        os.chdir(workdir)
        import tarfile
        tnm = "results_%s_%s_%s.tar.bz2" % (
            os.uname()[0], os.uname()[1], time.strftime("%Y-%m-%d_%H:%M"))
        t = tarfile.open(tnm, "w:bz2")
        t.add("tests_html")
        t.add("tests_html")
        t.close()
        if self.verbosity > 0:
            print("Packaged Result Info in:", tnm)
        tar_file = "{w}/{t}".format(w=workdir, t=tnm)
        if os.path.isfile(tar_file):
            ret_code = SUCCESS
        else:
            ret_code = FAILURE
        return ret_code

    def run(self, workdir, tests=None):
        """
        runs the specified test cases.
        If tests is None, runs the whole testsuite.

        workdir: top level project repo directory
        tests  : a space separated list of test cases
        """
        os.chdir(workdir)
        if tests is None:
            test_names = self._get_tests(workdir, self.args.tests)
        else:
            test_names = [tests]

        if self.args.checkout_baseline:
            ret_code = self._get_baseline(workdir)
            if ret_code != SUCCESS:
                return(ret_code)

        ret_code = self._do_run_tests(workdir, test_names)

        if self.args.html or self.args.package:
            self._generate_html(workdir)

        if self.args.package:
            self._package_results(workdir)

        return ret_code
