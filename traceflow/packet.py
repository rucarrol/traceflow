import socket
import struct
import logging
import random
import traceflow


class packet_encode:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        # TODO: Instead of passing all args in via kwargs, should actually explicitly set each attribute
        logging.debug("Init for packet_encode")
        if "ttl" not in kwargs.keys():
            print("ttl MUST be set")
            exit(1)
        if "ip_daddr" not in kwargs.keys():
            print("ip_daddr MUST be set")
            exit(1)

        if self.ip_ver == 4:
            # Do inet4 packet handling here
            ## Values which the kernel will set are here
            self.ip_tot_len = 0  # Kernel will set this value, thankfully
            self.ip_check = 0  # Kernel should set this value

            # Values we need to set now should be here
            self.ip_saddr = socket.inet_aton(
                socket.gethostbyname(
                    traceflow.socket_handler.get_egress_ip(self.ip_daddr)
                )
            )

            self.ip_daddr = socket.inet_aton(socket.gethostbyname(self.ip_daddr))

            # Finally, values that might have defaults overridden
            self.ip_tos = kwargs.get("ip_tos") if kwargs.get("ip_tos") else 0
            self.ip_frag_off = (
                kwargs.get("ip_frag_off") if kwargs.get("ip_frag_off") else 0
            )
            # If ip_id is not set, lets generate a random value here. 16 bit field means 65536
            self.ip_id = (
                kwargs.get("ip_id") if kwargs.get("ip_id") else random.randint(0, 65535)
            )
            self.ip_ihl = 5
            logging.debug(f"Sending with ID {self.ip_id}")
            logging.debug(f"Sending with TTL {self.ttl}")

        if self.ip_ver == 6:
            # TODO: All of the IPv6 things
            pass
        if self.l4_proto == socket.getprotobyname("udp"):
            # Do UDP Stuff here
            pass
        if self.l4_proto == socket.getprotobyname("tcp"):
            # Do TCP stuff here
            pass

    def get_ipid(self) -> int:
        return self.ip_id

    def encode_ipv4_header(self) -> bytes:
        """
        encode_ipv4_header uses all fields passed in __init__ to contruct a valid IPv4 Header

        :return: ip_header - bytes
        :rtype: bytes
        """
        # ip header fields
        # Source: https://www.binarytides.com/raw-socket-programming-in-python-linux/
        # Source: http://www.campergat.com/tcp-raw-sockets-in-python/
        logging.debug("Encoding IPv4 Packet now")
        # We add these bytes together so they equate to 8 bits wide, aka a "B" for struct.pack()
        ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl

        # the ! in the pack format string means network order
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            ip_ihl_ver,
            self.ip_tos,
            self.ip_tot_len,
            self.ip_id,
            self.ip_frag_off,
            self.ttl,
            self.l4_proto,
            self.ip_check,
            self.ip_saddr,
            self.ip_daddr,
        )
        return ip_header

    def encode_ipv4_udp_packet(self: object) -> bytes:
        """
        encode_ipv4_udp_packet encodes a valid (IPv4) UDP packet. The IPv4 limitation is due to IPv4 requiring a pseudo header
        where as IPv6 no longer requires src/dst IP address to be used as input to the checksum function.  

        :return: udp header, bytes + udp_data, the Payload
        :rtype: bytes
        """
        # Since we cannot determine the ip.id of the packet we send via socket.SOCK_DGRAM, we need to use raw sockets
        # To build a packet manually. This is the only way that I can see where we will know the ip.id in advance
        # Taken inspiration from  https://github.com/houluy/UDP/blob/master/udp.py
        # Generate some data, encode to bytes array, snag the length. Ensure data is even length, otherwise we have to add padding byte
        # TODO: Encode timestamp here for future analysis
        logging.debug("Encoding UDP Packet now")
        self.data = "0123456789".encode()
        # UDP is a bit stupid, and takes a lower layer info as part of it's checksum. Specifically src/dst IP addr.
        # This is called the pseudo header
        pseudo_header = struct.pack(
            "!BBH", 0, socket.getprotobyname("udp"), len(self.data) + 8
        )
        pseudo_header = self.ip_saddr + self.ip_daddr + pseudo_header
        # Set the checksum to 0, so we can generate a header, then calculate the checksum and re-apply
        checksum = 0
        udp_header = struct.pack(
            "!4H", self.udp_src_port, self.udp_dst_port, len(self.data) + 8, checksum
        )
        checksum = self._checksum_func(pseudo_header + udp_header + self.data)
        udp_header = struct.pack(
            "!4H", self.udp_src_port, self.udp_dst_port, len(self.data) + 8, checksum
        )
        return udp_header + self.data

    @staticmethod
    def _checksum_func(data: bytes) -> int:
        """
        _checksum_func is an internal method to perform 1s compliment checksum calculation for TCP/UDP headers

        :rtype: int
        :param data: A byte object which represents the header for checksum calculation
        :return: checksum: an int representing the checksum of the bytes/header.
        """
        # https://github.com/houluy/UDP/blob/master/udp.py#L120
        checksum = 0
        data_len = len(data)
        if data_len % 2:
            data_len += 1
            data += struct.pack("!B", 0)

        for i in range(0, data_len, 2):
            w = (data[i] << 8) + (data[i + 1])
            checksum += w

        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum = ~checksum & 0xFFFF
        return checksum


class packet_decode:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def decode_ipv4_header(header: bytes) -> dict:
        """
        decode_ipv4_header decodes a bytes object into an dict, containing the IPv4 fields.
        We use the Reference RFC 791 here : https://tools.ietf.org/html/rfc791
        #    0                   1                   2                   3
        #    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |Version|  IHL  |Type of Service|          Total Length         |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |         Identification        |Flags|      Fragment Offset    |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |  Time to Live |    Protocol   |         Header Checksum       |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |                       Source Address                          |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |                    Destination Address                        |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |                    Options                    |    Padding    |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        :param header: A bytes object containing an IPv4 header.
        :return: ret: a dict containing the fields in the IPv4 header
        """

        # Decode the first 20 bytes, rest will most likely be payload (We'll re-base with ip_ihl later on)
        logging.debug("Decoding IPv4 Header")
        ip_header = header[0:20]
        ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ttl, l4_proto, ip_check, ip_saddr, ip_daddr = struct.unpack(
            "!BBHHHBBH4s4s", ip_header
        )
        # since we cannot read nibbles easy, we need to take the first byte and take the high/low nibble out
        ip_ver = ip_ihl_ver >> 4
        ip_ihl = ip_ihl_ver & 0x0F  # 0x0F == 15
        # Internet Header Length is the length of the internet header in 32bit words, and thus points to the beginning of the data.
        # Note that the minimum value for a correct header is 5. We are re-basing this here to ensure we read the correct offset for payload
        ip_payload_offset = int((ip_ihl * 32) / 8)
        ret = {
            "ip_ihl": ip_ihl,
            "ip_ver": ip_ver,
            "ip_tos": ip_tos,
            "ip_tot_len": ip_tot_len,
            "ip_id": ip_id,
            "ip_frag_off": ip_frag_off,
            "ttl": ttl,
            "l4_proto": l4_proto,
            "ip_check": ip_check,
            "ip_saddr": socket.inet_ntoa(ip_saddr),
            "ip_daddr": socket.inet_ntoa(ip_daddr),
            "payload": header[ip_payload_offset:],
        }
        return ret

    @staticmethod
    def decode_ipv4_udp_packet(header: bytes) -> dict:
        """
        decode_ipv4_udp_packet takes a bytes object and decodes it into a UDP header (And payload).
        Reference here is  https://tools.ietf.org/html/rfc768
        #
        #                  0      7 8     15 16    23 24    31
        #                 +--------+--------+--------+--------+
        #                 |     Source      |   Destination   |
        #                 |      Port       |      Port       |
        #                 +--------+--------+--------+--------+
        #                 |                 |                 |
        #                 |     Length      |    Checksum     |
        #                 +--------+--------+--------+--------+
        #                 |
        #                 |          data octets ...
        #                 +---------------- ...

        :param header:
        :return:
        """

        logging.debug("Decoding UDP Header")
        udp_src_port, udp_dst_port, len_data, checksum = struct.unpack(
            "!4H", header[:8]
        )
        # UDP strikes again.
        len_data = len_data - 8
        data = header[8:]
        ret = {
            "src_port": udp_src_port,
            "dst_port": udp_dst_port,
            "length": len_data,
            "payload": data,
        }
        return ret

    @staticmethod
    def decode_icmp(header: bytes) -> dict:
        """
        decode_icmp decodes a bytes object into an ICMP message. This in itself should contain 64 bytes of a subpacket
        # RFC https://tools.ietf.org/html/rfc792
        #    0                   1                   2                   3
        #    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |     Type      |     Code      |          Checksum             |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |                             unused                            |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        #   |      Internet Header + 64 bits of Original Data Datagram      |
        #   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        :return: ret, a dict object of the fields in the ICMP header
        """

        logging.debug("Decoding ICMP Header")
        type, code, checksum, unused = struct.unpack("!BBHH", header[:6])
        # Payload should start after 2 machine words, which is 2 * 4 * 8
        payload = header[8:]
        ret = {
            "type": type,
            "code": code,
            "checksum": checksum,
            "unused": unused,
            "payload": payload,
        }
        return ret
