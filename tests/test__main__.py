import unittest
import traceflow.helpers as helpers


class Test__main__(unittest.TestCase):
    def test_ipid_to_ints(self):
        (i, j) = helpers.ipid_to_ints(257)
        self.assertIsInstance(i, int)
        self.assertIsInstance(j, int)
        self.assertEqual(i, 1)
        self.assertEqual(j, 1)

    def test_ints_to_ipid(self):
        ipid = helpers.ints_to_ipid(1, 1)
        self.assertIsInstance(ipid, int)
        self.assertEqual(ipid, 257)


if __name__ == "__main__":
    unittest.main()
