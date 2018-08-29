from distutils.core import setup

setup(name="testrunner",
      author="AIMS Software Team",
      description="Utilities for running nose-based test suites",
      url="http://github.com/cdat/TestsRunner",
      packages=['testsrunner'],
      package_dir={'testsrunner': 'lib'},
      data_files=[("share/testsrunner",
                   ["resources/testsrunner.json", "resources/image-compare.min.js", "resources/diff.html", "resources/test_options_file.json"])],
      )
