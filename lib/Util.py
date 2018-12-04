import os
import sys
import subprocess
import shlex
import hashlib
import time
import requests

SUCCESS = 0


def run_command(command, join_stderr=True, verbosity=2,
                popen_bufsize=0, env=None):

    if isinstance(command, str):
        command = shlex.split(command)
    if verbosity > 0:
        print("Executing %s in %s" % (" ".join(command), os.getcwd()))
    if join_stderr:
        stderr = subprocess.STDOUT
    else:
        stderr = subprocess.PIPE

    extra_keywords = {}
    if env is not None:
        extra_keywords["env"] = env
    P = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr,
                         bufsize=popen_bufsize, cwd=os.getcwd(),
                         **extra_keywords)
    out = []
    while P.poll() is None:
        read = P.stdout.readline().rstrip()
        decoded_str = read.decode('utf-8')
        out.append(str(decoded_str))
        if verbosity > 1 and len(read) != 0:
            print(read)

    ret_code = P.returncode
    if ret_code != SUCCESS:
        print("FAILED...cmd: {c}".format(c=command))
    return ret_code, out


def get_sampledata_path(setup_env_variables=None, default_path=None):
    """Return default path where sample data should be sitting
    defaults to sys.prefix/share/testsrunner/sample_data
    But sys.prefix can be overwritten by the firs tvariable found in the list passed by setup_env_variables
    The rest of the path can be overwritten via default_path
    :type setup_env_variables: `list` or `str`
    :type default_path: `str`
    """
    if setup_env_variables is None:
        setup_env_variables = ["TESTSRUNNER_SETUP_PATH"]
    # Make sure we passed a list of env variables, not just one
    if not isinstance(setup_env_variables, (list,tuple)):
        setup_env_variables = list(setup_env_variables)
    sampledata_path = None
    for env in setup_env_variables:
        sampledata_path = os.environ.get(env, None)
        if sampledata_path is not None:
            break
    if sampledata_path is None:
        sampledata_path = sys.prefix
    if default_path is None:
        default_path = os.path.join("share", "testsrunner", "sample_data")
    return os.path.join(env, default_path)


def download_sample_data_files(files_md5, path=None,
                               setup_env_variables=None,
                               default_path=None):
    """ Downloads sample data listed in <files_md5>
    into the specified <path>.
    If <path> is not set, it will download it to a default download
    directory specified by os.path.join(setup_env_variables, default_path)
    where setup_env_variables is actually a list of env variables to look at.

    :Example:

    ... doctest:: download_sample_data

    >>> import os # use this to check if sample data already exists
    >>> cdat_info.download_sample_data_files()

    :param path: String of a valid filepath.
    If None, sample data will be downloaded into the
    vcs.sample_data directory.
    :type path: `str`_ or `None`_
    :type setup_env_variables: `list` or `str`
    :type default_path: `str`
    """
    print("MD5:", files_md5)
    if not os.path.exists(files_md5) or os.path.isdir(files_md5):
        raise RuntimeError(
            "Invalid file type for list of files: %s" %
            files_md5)
    if path is None:
        path = get_sampledata_path()

    samples = open(files_md5).readlines()

    if len(samples[0].strip().split()) > 1:
        # Old style
        download_url_root = "https://cdat.llnl.gov/cdat/sample_data/"
        n0 = 0
    else:
        download_url_root = samples[0].strip()
        n0 = 1

    for sample in samples[n0:]:
        good_md5, name = sample.split()
        local_filename = os.path.join(path, name)
        try:
            os.makedirs(os.path.dirname(local_filename))
        except BaseException:
            pass
        attempts = 0
        while attempts < 3:
            md5 = hashlib.md5()
            if os.path.exists(local_filename):
                f = open(local_filename, "rb")
                md5.update(f.read())
                if md5.hexdigest() == good_md5:
                    attempts = 5
                    continue
            print("Downloading: '%s' from '%s' in: %s" % (name,
                                                          download_url_root,
                                                          local_filename))
            r = requests.get("%s/%s" % (download_url_root, name), stream=True)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter local_filename keep-alive new chunks
                        f.write(chunk)
                        md5.update(chunk)
            f.close()
            if md5.hexdigest() == good_md5:
                attempts = 5
            else:
                attempts += 1


def run_nose(opts, verbosity, test_name):
    command = ["nosetests", ] + opts + ["-s", test_name]
    if "--with-coverage" in opts:
        test_env = os.environ.copy()
        test_env["COVERAGE_FILE"] = os.path.join(
            ".cvrg", os.path.basename(test_name))
    else:
        test_env = None
    start = time.time()
    ret_code, out = run_command(command, True, verbosity, env=test_env)
    end = time.time()
    return {test_name: {"result": ret_code, "log": out, "times": {
        "start": start, "end": end}}}
