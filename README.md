# traceflow

[![Build Status](https://travis-ci.org/rucarrol/traceflow.png)](https://travis-ci.org/rucarrol/traceflow)


## Intro

`traceflow` is a utility written for educational purposes. 

`traceflow` which attempts to enumerate the number of paths between this host and a given destination. The mechanism for this is by not varying the destination source or destination port by TTL, thus keeping the inputs to any flow hashing calculations by routers along the path consistent for a single run. Then for each new run, vary the source port. 

By using raw sockets, `traceflow` can set the `IP.ID` of egress IP packets to both the Path ID and TTL, thus enabling us to match up return packets to a path easily. 

The goal is to develop this utility to a point where it can be useful in production networks to detect the following:

- Pre/post maintanace path changes
- as-path relax scenarios across IXPs/ISPs
- IP Topology discovery and visualisation


## Usage

Usage should be designed to be as straight forward as possible. 

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

More detailed help available in  `--help`.


## Why 

I wanted to learn more about raw sockets, traceroute and also wanted to try vary traceroute to be more flow/path aware, rather than hop aware. 

## TODO

- Better output formatting
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
