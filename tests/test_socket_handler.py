import unittest
import traceflow
import struct
import socket


class TestSocketHandler(unittest.TestCase):
    def test_egress_ip(self):
        i = traceflow.socket_handler.get_egress_ip("1.1.1.1")
        self.assertIsInstance(i, str)

    def test_init(self):
        i = traceflow.socket_listener("1.1.1.1")
        self.assertIsInstance(i, traceflow.socket_listener)

    def test_get_all_packets(self):
        i = traceflow.socket_listener("1.1.1.1")
        j = i.get_all_packets()
        self.assertIsInstance(j, dict)


if __name__ == "__main__":
    unittest.main()
