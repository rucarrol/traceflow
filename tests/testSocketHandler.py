import unittest
import traceflow
import struct
import socket


class TestSocketHandler(unittest.TestCase):
    def test_egress_ip(self):
        i = traceflow.socket_handler.get_egress_ip("1.1.1.1")
        self.assertIsInstance(i, str)


if __name__ == "__main__":
    unittest.main()
