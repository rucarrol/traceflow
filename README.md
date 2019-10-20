# traceflow

[![PyPI version](https://img.shields.io/pypi/v/traceflow.svg)](https://pypi.org/project/traceflow/)
[![PyPI downloads](https://img.shields.io/pypi/dm/traceflow.svg)](https://pypistats.org/packages/traceflow)
[![Build Status](https://travis-ci.org/rucarrol/traceflow.svg)](https://travis-ci.org/rucarrol/traceflow)
[![Coverage Status](https://coveralls.io/repos/github/rucarrol/traceflow/badge.svg)](https://coveralls.io/github/rucarrol/traceflow)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub](https://img.shields.io/github/license/rucarrol/traceflow.svg)](LICENSE)

## Intro

`traceflow` is a utility written for educational purposes.

`traceflow` which attempts to enumerate the number of paths between this host and a given destination. The mechanism for this is by not varying the destination source or destination port by TTL, thus keeping the inputs to any flow hashing calculations by routers along the path consistent for a single run. Then for each new run, vary the source port.

By using raw sockets, `traceflow` can set the `IP.ID` of egress IP packets to both the Path ID and TTL, thus enabling us to match up return packets to a path easily.

The goal is to develop this utility to a point where it can be useful in production networks to detect the following:

- Pre/post maintanace path changes
- as-path relax scenarios across IXPs/ISPs
- IP Topology discovery and visualisation


## Installation

`traceflow` can be installed via pip:

```
pip install traceflow
```

Alternatively, you can build from source and install manually:

```
python3 setup.py bdist_wheel
pip install ./dist/traceflow*any.whl
```

## Usage

Usage should be designed to be as straight forward as possible. There are currently 3 output formats supported - Vertical Output (`--format=vert`), Horizontal output(`--format=horiz`) and experimental Vis.js/Browser based output(`--format=viz`).

```
$ python3 traceflow.py www.telia.se
Resolved www.telia.se to 81.236.63.162
Looking at Path ID 1 (src port:33453 , dst port:33452)
Looking at Path ID 2 (src port:33454 , dst port:33452)
Looking at Path ID 3 (src port:33455 , dst port:33452)
Looking at Path ID 4 (src port:33456 , dst port:33452)
TTL:              | 1                 | 2                 | 3                 | 4                 | 5                 | 6                 | 7                 | 8                 | 9                 | 10                | 11                | 12                | 13                |
Path ID 1         | 192.168.0.1       | 84.116.236.63     | 84.116.239.133    | 62.115.172.136    | 62.115.120.100    | 80.91.249.11      | 213.155.130.101   | 80.91.245.159     | 62.115.123.159    | 81.228.88.48      | 81.228.84.173     | 81.228.94.41      | 90.228.166.164    |
Path ID 2         | 192.168.0.1       | 84.116.236.63     | 84.116.239.133    | 62.115.172.136    | 62.115.120.100    | 80.91.249.11      | 213.155.130.101   | 62.115.142.215    | 62.115.123.163    | 81.228.88.128     | 81.228.84.173     | 81.228.94.41      | 90.228.166.164    |
Path ID 3         | 192.168.0.1       | 84.116.236.63     | 84.116.239.133    | 62.115.172.136    | 62.115.120.100    | 80.91.249.11      | 213.155.130.101   | 62.115.121.15     | 62.115.123.159    | 81.228.88.48      | 81.228.84.173     | 81.228.94.41      | 90.228.166.164    |
Path ID 4         | 192.168.0.1       | 84.116.236.63     | 84.116.239.133    | 62.115.172.136    | 62.115.120.100    | 80.91.249.11      | 213.155.130.101   | 62.115.142.215    | 62.115.123.163    | 81.228.91.142     | 81.228.84.173     | 81.228.94.41      | 90.228.166.164    |
```

An example of vis.js outputs is as follows:

![vis.js](https://github.com/rucarrol/traceflow/raw/master/docs/traceflow_vis.png)

More detailed help available in  `--help`.

## Docker

`traceflow` can also be ran as a Docker container.

The latest version of traceflow is also on Docker Hub (https://hub.docker.com/r/awlnx/traceflow).

```
$ docker run -i -t awlnx/traceflow www.telia.se
```

To host the vis.js output through Docker:

```
$ docker run -p 127.0.0.1:8081:8081 -i -t awlnx/traceflow --format=viz --bind=0.0.0.0 www.telia.se
```

Note that it is required to bind the web server to the address of a public interface (inside the container) to be able to reach the web page.

To build it on your local machine do the following:

```
$ docker build -t traceflow .
```

## Why

I wanted to learn more about raw sockets, traceroute and also wanted to try vary traceroute to be more flow/path aware, rather than hop aware.

## Protocol used

The classical traceroutes (Dublin, Paris) attempt to enumerate the hops along a path by using many different entropy sources in the IP and UDP/TCP headers.

These days, most networks are using 3-tuple hashing in their forwarding decisions for load balancing: src/dst IP, proto, src/dst Port.

`traceflow` does the exact opposite here. We only vary two fields on each run - IP.ID, TTL. Then for subsequent runs, we only vary the UDP source port. Thus we can attempt to reliably test which flows would normally be combined into one output from traceroute, Paris traceroute and Dublin traceroute.

To detect return packets, we use the IP.ID in the IP header to store state - the path ID we're looking up, and the TTL of the egress packet. This allows us to implement a much faster multithreaded approach, as well as detect uneven hashing. It does bring a downside of being a bit more chatty than regular traceroute.

This idea came to me in Stockholm, so I would like to call it Stockholm traceroute.


## Features

- Pure python3, only 1 single external dependency (argparse)
- Multi-threaded approach, we no longer need to wait for a return packet for each probe
- Will identify and print unique paths in three different formats (Including browser based)
- Detects uneven path lengths
- Has a packet encoding and decoding library



## TODO

- Duplicate path detection
- IPv6 Support
- MPLS Support (Sending and decoding)
- TCP Support (Currently UDP only)
- Support for vis.js
- Understand raw sockets on OSX correctly to add support
- Test on Windows
- Add more resiliance to the code
- Implement ICMP probes to detect hosts which dont generate Port Unreachable
- Time stamps / latency


## Bugs

- Currently not very good at handling unequal length paths
- Darwin/OSX not functional yet
- Probably lots more

## Debugging

It's possible to pass the `--debug` flag for very verbose logging.
