""" A simple TCP server listener. """
import socket
import asyncio
from multiprocessing.connection import Connection


async def handle_echo(reader, writer):
    """ Echoes any data sent to the server back to the sender. """
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info("peername")

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()


async def listen(funnel: Connection):
    """ Runs a persistent server. """
    server = await asyncio.start_server(handle_echo, "127.0.0.1", 8888)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(listen())
