import unittest
import os
import subprocess
import shlex


class TestFlake8(unittest.TestCase):

    def testFlake8(self):
        pth = os.path.dirname(__file__)
        pth = os.path.join(pth, "..")
        pth = os.path.abspath(pth)
        pth = os.path.join(pth, "testsrunner")
        print()
        print()
        print()
        print()
        print("---------------------------------------------------")
        print("RUNNING: flake8 on directory %s" % pth)
        print("---------------------------------------------------")
        print()
        print()
        print()
        print()
        P = subprocess.Popen(shlex.split("flake8 --show-source --statistics --ignore=F841,E501 --max-line-length=120 %s" % pth),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        P.wait()
        out = P.stdout.read()
        if out != "":
            print(out)
        self.assertEqual(len(out), 0)
