# -*- coding: utf-8 -*-

""" Generic collection of helpers for __main__.py """

import argparse
import struct
import logging


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
        help="Print the results vertically (--format=vert) or horizontally (--format=horiz), or even represented in a web browser (--format=viz)",
        default="vert",
        type=str,
    )
    parser.add_argument(
        "--bind",
        help="IP address to bind the vis.js web server to",
        default="127.0.0.1",
        type=str,
    )
    parser.add_argument(
        "--dedup", help="De-duplicate the traceflow results", action="store_true"
    )
    parser.add_argument("--debug", help="Enable Debug Logging", action="store_true")

    # Positional Arguments
    parser.add_argument("destination", action="store", type=str)

    args = parser.parse_args()
    return args


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


def remove_duplicates(traces: dict, daddr: str) -> dict:
    """
    remove_duplicates takes traces (dict containing traces) and daddr(str destination address) and removes any duplicate
    entries at the end of the trace.

    :param traces: a dict of paths and traces
    :param daddr: A string, destination IP address
    :return: dict: cleaned up traces dict
    """
    for path in traces.keys():
        # Remove any duplicate answers from daddr
        dup_keys = [i for i in traces[path] if traces[path][i] == daddr]
        while len(dup_keys) > 1:
            logging.debug("dup keys: %s" % dup_keys)
            traces[path].pop(max(dup_keys))
            dup_keys = [i for i in traces[path] if traces[path][i] == daddr]
    return traces


def remove_duplicate_paths(traces: dict) -> dict:
    """
    remove_duplicate_paths takes traces (dict containing traces) and removes any duplicate path.

    :param traces: a dict of paths and traces
    :return: dict: a deduplicated list of paths
    """
    dedup = dict()
    seen = list()
    for path in sorted(traces.keys()):
        # Create a list (ordered) which we'll insert the hop at index of TTL-1
        total_path = list()
        for ttl in sorted(traces[path].keys()):
            total_path.append(traces[path][ttl])
        # If we have not seen this list before, insert it into seen, then
        if total_path not in seen:
            seen.append(total_path)
            # we recreate the dict in dedup
            for ttl, hop in enumerate(total_path):
                # And add the trace with the first path we've seen it at
                if path not in dedup.keys():
                    dedup[path] = dict()
                dedup[path].update({ttl + 1: hop})
        logging.debug(f"Found unique path: {path}")
    return dedup
