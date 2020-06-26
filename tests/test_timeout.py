import unittest
import time


class TestTimeout(unittest.TestCase):

    def testTimeout(self):
        time.sleep(5)
        print("...testPass...")
        self.assertEqual(0, 0)
