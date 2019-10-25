#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import traceflow
import time
import logging
import socket
import traceflow.helpers as helpers


def main():
    # ha ha ha
    args = helpers.get_help()

    # CLI arguments set here.
    try:
        daddr = socket.gethostbyname(args.destination)
    except socket.gaierror as e:
        if "Name or service not known" in str(e):
            print(f"Error, could not resolve {args.destination}, exiting")
            exit(1)
        else:
            print(f"General error resolving {args.destination}")
            print("exiting")
            exit(1)
    print(f"Resolved {args.destination} to {daddr}")
    TOT_RUNS = args.paths
    DST_PORT = args.dstport
    SRC_PORT = args.srcport
    MAX_TTL = args.ttl
    BIND_IP = args.bind

    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    if TOT_RUNS > 255:
        print(f"Max paths we can probe is 255. Setting --paths to 255 and continuing")
        TOT_RUNS = 255
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
            ip_id = helpers.ints_to_ipid(path, ttl)
            # TODO: Hide this behind a class
            ip_ver = 4
            ip_daddr = daddr
            udp_src_port = port
            udp_dst_port = DST_PORT
            ttl = ttl
            l4_proto = 17
            ip_id = ip_id
            additional_params = {"ip_tos": None, "ip_frag_off": None}
            # Create our packet here.
            i = traceflow.packet_encode(
                ip_ver,
                ip_daddr,
                udp_src_port,
                udp_dst_port,
                ttl,
                l4_proto,
                ip_id,
                **additional_params,
            )
            # TODO: Maybe refactor to hide these behind a single function, to be v4/v6 agnostic
            # Combine the IPv4 and UDP headers here
            probe = i.encode_ipv4_header() + i.encode_ipv4_udp_packet()

            s = traceflow.socket_handler(ip_daddr)
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
    if len(rx_icmp) == 0:
        logging.debug(f"rx_icmp is  {len(rx_icmp)}")
        print(f"Did not receive any TTL expired ICMP packets. Exiting")
        exit(1)
    traces = dict()

    # For each packet the listener got, loop across the ICMP message and see what the TTL/Path combo is.
    # Then add them to the dict traces as: traces[path][ttl]
    for i in rx_icmp:
        icmp_packet = traceflow.packet_decode.decode_icmp(rx_icmp[i]["payload"])
        ipv4_packet = traceflow.packet_decode.decode_ipv4_header(icmp_packet["payload"])
        (path, ttl) = helpers.ipid_to_ints(ipv4_packet["ip_id"])
        if path not in traces.keys():
            traces[path] = dict()
        if ttl not in traces[path].keys():
            traces[path][ttl] = rx_icmp[i]["ip_saddr"]
        logging.debug("Run: %s TTL: %s" % (path, ttl))

    # Here we will fill in missing probes with a *
    # We should also trim any duplicate replies from daddr
    # and also fill in an x to pad up unequal path lengths
    traces = helpers.remove_duplicates(traces, daddr)
    path_max = max([max(traces[i].keys()) for i in traces.keys()])
    for path in traces.keys():
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

    if args.dedup:
        traces = helpers.remove_duplicate_paths(traces)
    if args.format.lower() == "vert":
        # Print horizontal results
        traceflow.printer.print_vertical(traces)
    if args.format.lower() == "horiz":
        # print vertical results
        traceflow.printer.print_horizontal(traces)
    if args.format.lower() == "viz":
        # Experimental vis.js / browser based visualisation
        traceflow.printer.start_viz(traces, BIND_IP)
    exit(0)


if __name__ == "__main__":
    main()
