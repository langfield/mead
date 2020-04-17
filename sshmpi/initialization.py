""" Functions for initializing client connections. """
import os
import time
import socket
import multiprocessing as mp
from typing import List

from pssh.utils import read_openssh_config
from pssh.clients import ParallelSSHClient
from sshmpi.utils import get_available_hostnames_from_sshconfig
from sshmpi.spout import multistream_to_head
from sshmpi.tcp_listener import listener


# TODO: Use this instead of SSH config to make setup more explicit.
def get_nodes() -> List[str]:
    """ Read hostnames of remote nodes. """
    nodes_path = os.path.expanduser("~/nodes.json")
    with open(nodes_path, "r") as nodes_file:
        lines = nodes_file.read().split("\n")
        print(lines)
    return lines


def init():
    """ Public-facing API for SSHMPI initialization. """
    # Define private key path and hostnames.
    pkey = os.path.expanduser("~/.ssh/id_rsa")

    hosts = get_available_hostnames_from_sshconfig()
    print("Hosts:", hosts)

    # Per-host config dictionaries.
    config = {}
    for hostname in hosts:
        _, _, port, _ = read_openssh_config(hostname)
        config[hostname] = {"port": port}

    localhost = socket.gethostname()
    client = ParallelSSHClient(hosts, host_config=config, pkey=pkey)
    output: dict = client.run_command("./spout --hostname %s" % localhost)
    stdins = [out.stdin for out in output.values()]
    print("Finished initialization.")

    # Bytes coming out of ``in_spout`` are from a remote host.
    in_funnel, in_spout = mp.Pipe()
    out_funnel, out_spout = mp.Pipe()

    # The listener will dump bytes sent to ``127.0.0.1:8888`` into the funnel.
    p_in = mp.Process(target=listener, args=(in_funnel,))
    p_in.start()

    p_out = mp.Process(target=multistream_to_head, args=(out_spout, stdins))
    p_out.start()

    data = "Hello out there."
    out_funnel.send(data)

    print("Sent data through funnel.")

    # Display the output.
    for host, out in output.items():
        for line in out.stdout:
            if line.strip():
                print("Host %s: %s" % (host, line))
        for line in out.stderr:
            if line.strip():
                print("Host %s: %s" % (host, line))

    while 1:
        reply = in_spout.recv()
        print("RE:", reply)