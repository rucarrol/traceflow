#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import traceflow
import time
import struct
import logging
import argparse
import socket


def ipid_to_ints(ipid: int) -> tuple:
    """
    ipid_to_ints splits the ip.id of an ingress packet (Half Word, aka 16 bits) into two ints between 0 and 255.
    :param ipid: int which is 16 bits in size.
    :return: tuple:
    """
    b = ipid.to_bytes(2, byteorder="big")
    return struct.unpack("!BB", b)


def ints_to_ipid(path: int, ttl: int) -> int:
    """
    ints_to_ipid takes to ints of 8 bits size (0 to 255) and combines them into a Half Word, which is then converted into an int

    :param path: the Path this ipid corresponds to
    :param ttl: the TTL of the egress packet
    :return: int: path and ttl combined into a halfword
    """
    s = struct.pack("!H", (path << 8) + ttl)
    return int.from_bytes(s, byteorder="big")


def help_text() -> str:
    message: str = """
    TraceFlow is a utility which attempts to enumerate the number of paths between this host and a given destination.
    Please use --help for more verbose help and options"""
    return message


def get_help() -> argparse:
    """
    Helper function to handle CLI arguments.

    :return: argparse: parsed arguments
    """
    message = help_text()
    parser = argparse.ArgumentParser(message)

    # Named Arguments
    parser.add_argument(
        "--paths", help="Number of paths to enumerate", default=4, type=int
    )
    parser.add_argument("--ttl", help="Max TTL to reach", default=64, type=int)
    parser.add_argument(
        "--srcport", help="Default Source Port to use", default=33452, type=int
    )
    parser.add_argument(
        "--dstport", help="Default Destination Port to use", default=33452, type=int
    )
    parser.add_argument(
        "--wait",
        help="Set the time (in seconds) to wait between sending probes",
        default=0.1,
        type=int,
    )
    parser.add_argument(
        "--format",
        help="Print the results vertically(--format=vert) or horizontally(--format=horiz)",
        default="vert",
        type=str,
    )
    parser.add_argument("--debug", help="Enable Debug Logging", action="store_true")

    # Positional Arguments
    parser.add_argument("destination", action="store", type=str)

    args = parser.parse_args()
    return args


def main():
    # ha ha ha
    args = get_help()

    # CLI arguments set here.
    daddr = socket.gethostbyname(args.destination)
    print(f"Resolved {args.destination} to {daddr}")
    TOT_RUNS = args.paths
    DST_PORT = args.dstport
    SRC_PORT = args.srcport
    MAX_TTL = args.ttl

    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    # Setup the background thread listener here. Note that we need to pass daddr so we can snag the dst port unreachable
    # ICMP message.
    listener = traceflow.socket_listener(daddr)

    run_ids = dict()

    # Keep track of which path we're looking to enumerate
    for path in range(1, TOT_RUNS + 1):
        port = SRC_PORT + path
        run_ids[path] = port
        print(f"Looking at Path ID {path} (src port:{port} , dst port:{DST_PORT})")
        for ttl in list(range(1, MAX_TTL)):
            # Here we will combine the path we're after with the TTL, and use this to track the returning ICMP payload
            ip_id = ints_to_ipid(path, ttl)
            # TODO: Hide this behind a class
            packet = {
                "ip_ver": 4,
                "ip_daddr": daddr,
                "udp_src_port": port,
                "udp_dst_port": DST_PORT,
                "ttl": ttl,
                "l4_proto": 17,
                "ip_id": ip_id,
            }
            # Create our packet here.
            i = traceflow.packet_encode(**packet)
            # TODO: Maybe refactor to hide these behind a single function, to be v4/v6 agnostic
            # Combine the IPv4 and UDP headers here
            probe = i.encode_ipv4_header() + i.encode_ipv4_udp_packet()

            s = traceflow.socket_handler(packet["ip_daddr"])
            _ = s.send_ipv4(probe)
            time.sleep(args.wait)
            # Since we are not running a sequential trace, we should check in to see if we've gotten a reply from the destination yet
            packets = listener.get_packets_by_pathid(path)
            end = [i for i in packets if i["ip_saddr"] == daddr]
            if len(end) > 0:
                logging.debug(f"Breaking trace to {daddr} at TTL {ttl}")
                break

    # We should get all the packets the listener received here
    rx_icmp = listener.get_all_packets()
    traces = dict()

    for i in rx_icmp:
        icmp_packet = traceflow.packet_decode.decode_icmp(rx_icmp[i]["payload"])
        ipv4_packet = traceflow.packet_decode.decode_ipv4_header(icmp_packet["payload"])
        (path, ttl) = ipid_to_ints(ipv4_packet["ip_id"])
        if path not in traces.keys():
            traces[path] = dict()
        if ttl not in traces[path].keys():
            traces[path][ttl] = rx_icmp[i]["ip_saddr"]
        logging.debug("Run: %s TTL: %s" % (path, ttl))

    # Here we will fill in missing probes with a *
    # We should also trim any duplicate replies from daddr
    # and also fill in an x to pad up unequal path lengths
    path_max = max([max(traces[i].keys()) for i in traces.keys()])
    for path in traces.keys():
        # Remove any duplicate answers from daddr
        dup_keys = [i for i in traces[path] if traces[path][i] == daddr]
        while len(dup_keys) > 1:
            logging.debug("dup keys: %s" % dup_keys)
            traces[path].pop(max(dup_keys))
            dup_keys = [i for i in traces[path] if traces[path][i] == daddr]
        # Now we fill in * for any missing hops
        last_ttl = sorted(traces[path])[-1]
        for ttl in list(range(1, last_ttl + 1)):
            if ttl not in traces[path]:
                logging.debug(f"Missing TTL({ttl}) for path {path}")
                traces[path][ttl] = "*"
        # Now we should handle unequal length paths
        path_length = len(traces[path])
        if path_length < path_max:
            for i in range(path_length, path_max + 1):
                if i not in traces[path].keys():
                    logging.debug(f"Insert fake hop at {i} for path {path}")
                    traces[path][i] = "x"

    if args.format.lower() == "vert":
        # Print horizontal results
        traceflow.printer.print_vertical(traces)
    if args.format.lower() == "horiz":
        # print vertical results
        traceflow.printer.print_horizontal(traces)
    if args.format.lower() == "viz":
        # Experimental vis.js / browser based visualisation
        traceflow.printer.start_viz(traces)
    exit(0)


if __name__ == "__main__":
    main()
