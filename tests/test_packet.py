import unittest
import traceflow
import struct
import socket


class TestPacketDecode(unittest.TestCase):
    def setUp(self):
        self.packet = b"E\xc0<\x00LT\x00\x009\x01q\xd0\x01\x01\x01\x01\xc0\xa8\x00\x1f\x03\x03\xbf\xf7\x00\x00\x00\x00E\x004\x00\xe8\xca\x00\x00\x01\x11\x0e&\xc0\xa8\x00\x1f\x01\x01\x01\x01\xe8\xb5\x82\xaf\x00 \xd1\x7f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    def test_decode_ipv4(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertIsInstance(i, dict)

    def test_decode_ipv4_ttl(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ttl"], 57)

    def test_decode_ipv4_saddr(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_saddr"], "1.1.1.1")

    def test_decode_ipv4_daddr(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_daddr"], "192.168.0.31")

    def test_decode_ipv4_ihl(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_ihl"], 5)

    def test_decode_ipv4_ver(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_ver"], 4)

    def test_decode_ipv4_ip_tos(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_tos"], 192)

    def test_decode_ipv4_tot_len(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_tot_len"], 15360)

    def test_decode_ipv4_ipid(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_id"], 19540)

    def test_decode_ipv4_frag_off(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_frag_off"], 0)

    def test_decode_ipv4_l4_proto(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["l4_proto"], 1)

    def test_decode_ipv4_checksum(self):
        i = traceflow.packet_decode.decode_ipv4_header(self.packet)
        self.assertEqual(i["ip_check"], 29136)


class TestPacketEncode(unittest.TestCase):
    def setUp(self):
        self.ip_ver = 4
        # UDP
        self.l4_proto = 17

        self.ip_daddr = "1.1.1.1"
        self.ip_saddr = traceflow.socket_handler.get_egress_ip(self.ip_daddr)

        self.udp_src_port = 35000
        self.udp_dst_port = 53

        self.ttl = 3

        # packet_encode(ip_ver, ip_daddr, udp_src_port, udp_dst_port, ttl, l4_proto, ip_id, **kwargs)
        self.test_encode_class_instance = traceflow.packet_encode(
            self.ip_ver,
            self.ip_daddr,
            self.udp_src_port,
            self.udp_dst_port,
            self.ttl,
            self.l4_proto,
            None,
        )

    # IPv4 Tests here
    def test_decode_ipv4(self):
        ipv4_hdr = self.test_encode_class_instance.encode_ipv4_header()
        self.assertIsInstance(ipv4_hdr, bytes)

    # ttl = 3
    def test_encode_ipv4_ttl(self):
        # TTL is 9th byte
        ttl = self.test_encode_class_instance.encode_ipv4_header()[8]
        self.assertEqual(ttl, 3)

    # l4_proto = 17
    def test_encode_ipv4_l4_proto(self):
        # Proto is 9th byte
        l4_proto = self.test_encode_class_instance.encode_ipv4_header()[9]
        self.assertEqual(l4_proto, 17)

    # Checksum is 9059 - pre-computed.
    # def test_encode_ipv4_l4_proto_fixed_checksum(self):
    # Checksum is 10th and 11th bytes
    # l4_proto = self.test_encode_class_instance.encode_ipv4_header()[10:12]
    # self.assertEqual(l4_proto, struct.pack("H", 9059))

    # ip_saddr = traceflow.socket_handler.get_egress_ip(ip_daddr)
    # This was pre-computed to 192.168.0.31 for this packet.
    # def test_encode_ipv4_l4_proto_local_ip(self):
    #     # Checksum is 10th and 11th bytes
    #     ip_saddr = self.test_encode_class_instance.encode_ipv4_header()[12:16]
    #     self.assertEqual(ip_saddr, socket.inet_aton("192.168.0.31"))

    # ip_daddr = "1.1.1.1"
    def test_encode_ipv4_l4_proto_public_ip(self):
        # Checksum is 10th and 11th bytes
        ip_saddr = self.test_encode_class_instance.encode_ipv4_header()[16:20]
        self.assertEqual(ip_saddr, socket.inet_aton("1.1.1.1"))

    # UDP Tests here
    def test_decode_udp(self):
        udp_hdr = self.test_encode_class_instance.encode_ipv4_udp_packet()
        self.assertIsInstance(udp_hdr, bytes)

    # udp_src_port = 35000
    def test_encode_udp_src(self):
        # src is 1st word
        udp_src_port = self.test_encode_class_instance.encode_ipv4_udp_packet()[0:2]
        self.assertEqual(udp_src_port, struct.pack("!H", 35000))

    # udp_dst_port = 53
    def test_encode_udp_dst(self):
        # dst is 2nd word
        udp_dst_port = self.test_encode_class_instance.encode_ipv4_udp_packet()[2:4]
        self.assertEqual(udp_dst_port, struct.pack("!H", 53))

    # UDP Packet Length: 18, computed.
    def test_encode_udp_len(self):
        # Len is 3rd word
        udp_len = self.test_encode_class_instance.encode_ipv4_udp_packet()[4:6]
        self.assertEqual(udp_len, struct.pack("!H", 18))


if __name__ == "__main__":
    unittest.main()
