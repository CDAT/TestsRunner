from distutils.core import setup
from subprocess import Popen, PIPE

Version = "1.0"
p = Popen(
    ("git",
     "describe",
     "--tags"),
    stdin=PIPE,
    stdout=PIPE,
    stderr=PIPE)
try:
    descr = p.stdout.readlines()[0].strip().decode("utf-8")
    Version = "-".join(descr.split("-")[:-2])
    if Version == "":
        Version = descr
except:
    descr = Version



scripts = [ 'scripts/print_something.py' ]


setup(name="testrunner",
      author="AIMS Software Team",
      version=descr,
      description="Utilities for running nose-based test suites",
      url="http://github.com/cdat/TestsRunner",
      packages=['testsrunner'],
      package_dir={'testsrunner': 'lib'},
      scripts=scripts,
      data_files=[("share/testsrunner",
                   ["resources/testsrunner.json", "resources/image-compare.min.js", "resources/diff.html",
                    "resources/coveragerc"])],
      )
