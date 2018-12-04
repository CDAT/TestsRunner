from setuptools import setup, find_packages
from subprocess import Popen, PIPE

scripts = [ 'scripts/print_something.py' ]

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


setup(name="testrunner",
      version=descr,
      author="AIMS Software Team",
      description="Utilities for running nose-based test suites",
      url="http://github.com/cdat/TestsRunner",
      packages=find_packages(),
      scripts=scripts,
      data_files=[("share/testsrunner",
                   ["resources/testsrunner.json", "resources/image-compare.min.js", "resources/diff.html",
                    "resources/coveragerc"])],
      )
