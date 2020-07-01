import unittest


class TestPassingTest(unittest.TestCase):

    def testPass(self):
        print("...testPass...")
        self.assertEqual(0, 0)
