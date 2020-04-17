import time
import pickle
import socket
import logging
import threading
import socketserver
import multiprocessing as mp
from multiprocessing.connection import Connection


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """ Handles incoming requests. """

    def handle(self):
        buf = b""
        while 1:
            # Read the length of the message given in 16 bytes.
            cur_thread = threading.current_thread()
            buf += self.request.recv(16)
            t = time.time()

            # Parse the message length bytes.
            blength = buf
            length = int(blength.decode("ascii"))

            # Read the message proper.
            buf = self.request.recv(length + 1)

            # Deserialize the data and send to the backward connection client.
            obj = pickle.loads(buf)
            self.server.funnel.send(obj)
            logging.info("SERVER: Unpickling time: %fs", time.time() - t)
            logging.info("SERVER: Received %s from remote %f", str(obj), time.time())

            # Reset buffer.
            buf = b""


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """ This just adds the ThreadingMixIn. """

    def __init__(self, *args, **kwargs):
        if "funnel" in kwargs:
            self.funnel = kwargs.pop("funnel")
        super().__init__(*args, **kwargs)


def client(ip, port, message):
    """ Dummy client to send test messages to the server. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, "ascii"))


def listener(funnel: Connection) -> None:
    """ Waits for data and pipes it to HNP via a ThreadedTCPServer. """
    host, port = "127.0.0.1", 8888
    # pylint: disable=broad-except
    try:
        server = ThreadedTCPServer(
            (host, port), ThreadedTCPRequestHandler, funnel=funnel
        )
        with server:
            ip, port = server.server_address

            # Start a thread with the server -- that thread will then start one
            # more thread for each request
            server_thread = threading.Thread(target=server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            server_thread.start()
            print("Server loop running in thread:", server_thread.name)

            while 1:
                time.sleep(1)
    except Exception as err:
        server.shutdown()
        raise err


def main() -> None:
    # Port 0 means to select an arbitrary unused port.
    host, port = "127.0.0.1", 8888
    funnel, spout = mp.Pipe()

    server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler, funnel=funnel)
    with server:
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        client(ip, port, "Hello World 1")
        client(ip, port, "Hello World 2")
        client(ip, port, "Hello World 3")

        while 1:
            response = spout.recv()
            print(response)

        server.shutdown()


if __name__ == "__main__":
    main()
