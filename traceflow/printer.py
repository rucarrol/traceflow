import json


class printer:
    def __init__(self):
        pass

    @staticmethod
    def print_vertical(traces):
        """
        print_vertical prints the results in a vertical manner.

        :param traces: dict
        """
        max_ttl = max([max(traces[i].keys()) for i in traces.keys()])
        row_format = "%-17s | "
        # Print header
        print(row_format % "TTL: ", end="")
        _ = [print(row_format % i, end="") for i in range(1, max_ttl + 1)]
        print("")
        # Print Body
        for path_id in sorted(traces.keys()):
            print(row_format % f"Path ID {path_id} ", end="")
            for hop in traces[path_id]:
                print(row_format % traces[path_id][hop], end="")
            print("")
        return None

    @staticmethod
    def print_horizontal(traces):
        """
        print_horizontal prints the results in a horizontal manner.

        :param traces: dict
        """
        # Get the MAX TTL value from the results
        max_ttl = max([max(traces[i].keys()) for i in traces.keys()])
        col_format = "%-17s | "
        # Print header
        # Spacer for the TTL column
        print(col_format % "", end="")
        for i in sorted(traces.keys()):
            print(col_format % format("Path ID: {0} ".format(i)), end="")
        print("")
        # Print Body
        for ttl in range(1, max_ttl + 1):
            print(col_format % format("TTL: {0}".format(ttl)), end="")
            for path_id in traces.keys():
                print(col_format % traces[path_id][ttl], end="")
            print("")
        return None

    @staticmethod
    def start_viz(traces) -> None:
        ## TODO: Break apart into different classes?
        import http.server

        port = 8081
        bind_ip = "127.0.0.1"
        DIRECTORY = "vars/"

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=DIRECTORY, **kwargs)

        nodes = printer.__build_nodes(traces)
        f = open(DIRECTORY + "nodes.json", "w")
        f.write("data = '{0}'".format(nodes))
        f.close()
        print(
            f"Starting temp. web server on http://{bind_ip}:{port}. Ctrl+C to finish/exit."
        )
        httpd = http.server.HTTPServer((bind_ip, port), Handler)
        httpd.serve_forever()
        return None

    @staticmethod
    def __build_nodes(traces: dict) -> dict:
        max_ttl = max([max(traces[i].keys()) for i in traces.keys()])
        nodes = dict()
        nodes["nodes"] = list()
        nodes["links"] = list()
        for path in traces.keys():
            for hop in traces[path].keys():
                node = dict()
                node["id"] = traces[path][hop]
                node["label"] = traces[path][hop]
                if node not in nodes["nodes"]:
                    nodes["nodes"].append(node)
                if hop < max_ttl:
                    link = dict()
                    link["from"] = traces[path][hop]
                    link["to"] = traces[path][hop + 1]
                    nodes["links"].append(link)
        return json.dumps(nodes)
