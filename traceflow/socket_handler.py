import socket
import threading
import logging
import platform
import traceflow
import struct


class socket_handler:
    def __init__(self, daddr):
        try:
            self.raw_sock = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW
            )
        except PermissionError as e:
            print(e)
            print("Please run as root!")
            exit(1)
        self.ip_daddr = daddr
        os_release = platform.system()
        if os_release == "Darwin":
            # Boned. TODO: Work on fixing this.
            logging.debug(
                "Detected Mac OS - Cannot support writing of raw IP packets, exiting"
            )
            exit(1)
        if os_release.endswith("BSD"):
            # BSD - Need to explicit set IP_HDRINCL. Probably.
            # See https://wiki.freebsd.org/SOCK_RAW
            self.raw_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            logging.debug("Detected a BSD")
        if os_release == "Linux":
            # Linux - No need to set IP_HDRINCL, but going to anyway!
            self.raw_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            logging.debug("Detected Linux")
        if os_release == "Windows":
            # No idea - No ability to test. Maybe abort?
            # TODO: Find testers?
            logging.debug("Detected NT")
            print("Untested on Windows - Exiting")
            exit(1)

    def send_ipv4(self, packet: bytes) -> int:
        """
        send_ipv4 is a thin wrapper around socket.sendto()
        :param packet: bytes object containing an IPv4 header, and encap'd proto packet (ie: udp/tcp)
        :return: int: the bits put on the wire
        """
        bits = self.raw_sock.sendto(packet, (self.ip_daddr, 0))
        return bits

    @staticmethod
    def get_egress_ip(daddr: bytes) -> str:
        """
        __get_egress_ip is an internal method to find out our egress address for a given destination
        TODO: Fixup for IPv6 compat.

        :param daddr: destination address in binary form
        :return: egress_ip_address, a string/quad dotted notation IPv4 address

        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((daddr, 1))  # connect() for UDP doesn't send packets
        egress_ip_address = s.getsockname()[0]
        logging.debug("Picked %s as egress IP" % egress_ip_address)
        s.shutdown(0)
        s.close()
        return egress_ip_address


class socket_listener:
    def __init__(self, ip_daddr):
        # We're only interested in ICMP, so happy to have this hard coded.
        try:
            self.icmp_listener = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp")
            )
        except PermissionError as e:
            print(e)
            print("Please run as root!")
            exit(1)
        self.ip_daddr = ip_daddr
        self.mutex = threading.Lock()
        logging.debug("Starting")
        self.icmp_packets = dict()
        t = threading.Thread(target=self.listener)
        t.setDaemon(True)
        t.start()

    def listener(self):
        """thread worker function"""
        logging.debug("Listening for ICMP...")
        while True:
            icmp_packet, curr_addr = self.icmp_listener.recvfrom(512)
            # Decode the IPv4 packet around the ICMP message
            i = traceflow.packet_decode.decode_ipv4_header(icmp_packet)
            # Decode the actual ICMP message inside the IPv4 packet
            icmp_packet_ret = traceflow.packet_decode.decode_icmp(i["payload"])
            # And decode the returning IPv4 packet which is the payload inside of the ICMP message
            ip_id = traceflow.packet_decode.decode_ipv4_header(
                icmp_packet_ret["payload"]
            )["ip_id"]
            # Did we get a TTL Expired (11)?
            if icmp_packet_ret["type"] == 11:
                logging.debug(
                    "Got TTL Expired from %s with ip_id %s" % (curr_addr[0], ip_id)
                )
                self.mutex.acquire()
                self.icmp_packets[ip_id] = i
                self.mutex.release()
            ## TODO: Correctly implement a "stop" here
            if curr_addr[0] == self.ip_daddr:
                self.mutex.acquire()
                self.icmp_packets[ip_id] = i
                self.mutex.release()

    def get_packet_by_ipid(self, ipid: int) -> dict:
        """
        get_packet_by_ipid will take in a specific ip.id and find the corresponding packet

        :param ipid: the ip.id of the packet in question
        :return: dict() which contains the corresponding IP packet
        """
        self.mutex.acquire()
        for packet in self.icmp_packets.keys():
            icmp_packet = traceflow.packet_decode.decode_icmp(
                self.icmp_packets[packet]["payload"]
            )
            ipv4_packet = traceflow.packet_decode.decode_ipv4_header(
                icmp_packet["payload"]
            )
            if ipid == ipv4_packet["ip_id"]:
                return icmp_packet
        self.mutex.release()
        return None

    def get_all_packets(self) -> list:
        """
        get_all_packets returns all currently captures packets.

        :return: list() of dicts()
        """
        self.mutex.acquire()
        i = self.icmp_packets
        self.mutex.release()
        return i

    def get_packets_by_pathid(self, path_id: int) -> list:
        """
        get_packets_by_runid depends on the fact that we intent to manually construct the IPID for each packet, so the
        top 8 bits correspond to a "run".

        :param run_id: an int which is 8 bits in size and corresponds to a path.
        :return: list of packets
        """
        packets = list()
        self.mutex.acquire()
        for packet in self.icmp_packets.keys():
            icmp_packet = traceflow.packet_decode.decode_icmp(
                self.icmp_packets[packet]["payload"]
            )
            ipv4_packet = traceflow.packet_decode.decode_ipv4_header(
                icmp_packet["payload"]
            )
            b = ipv4_packet["ip_id"].to_bytes(2, byteorder="big")
            (run, ttl) = struct.unpack("!BB", b)
            if run == path_id:
                packets.append(self.icmp_packets[packet])
        self.mutex.release()
        return packets
