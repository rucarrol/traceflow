import unittest
import traceflow.helpers as helpers
import argparse


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

    def test_help_text(self):
        helptext = helpers.help_text()
        self.assertIsInstance(helptext, str)

    def test_get_help(self):
        args = helpers.get_help()
        self.assertIsInstance(args, argparse.Namespace)

    def test_remove_duplicates(self):
        duplicate_paths = {1: {1: "1.1.1.1", 2: "1.1.1.1"}}
        dedup_example = {1: {1: "1.1.1.1"}}
        dedup_result = helpers.remove_duplicates(duplicate_paths, "1.1.1.1")
        self.assertDictEqual(dedup_example, dedup_result)

    def test_remove_duplicate_paths(self):
        duplicate_paths = {
            1: {
                1: "1.1.1.1",
                2: "2.2.2.2",
                3: "3.3.3.3",
                4: "4.4.4.4",
                5: "5.5.5.5",
                6: "6.6.6.6",
            },
            2: {
                1: "1.1.1.1",
                2: "2.2.2.2",
                3: "3.3.3.3",
                4: "4.4.4.4",
                5: "5.5.5.5",
                6: "6.6.6.6",
            },
        }
        dedup_example = {
            1: {
                1: "1.1.1.1",
                2: "2.2.2.2",
                3: "3.3.3.3",
                4: "4.4.4.4",
                5: "5.5.5.5",
                6: "6.6.6.6",
            }
        }
        dedup_result = helpers.remove_duplicate_paths(duplicate_paths)
        self.assertDictEqual(dedup_example, dedup_result)


if __name__ == "__main__":
    unittest.main()
