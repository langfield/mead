""" A function for transforming an arbitrary python object into a byte sequence. """
import pickle


def get_parcel(obj: object) -> bytes:
    """ Pickles an object and returns bytes of a length+message pair. """
    message = pickle.dumps(obj)

    # Get representation of then length of ``message`` in bytes.
    length = str(len(message)).encode("ascii")
    assert len(length) <= 16

    # Compute the pad so that prefix is a 16-byte sequence.
    padsize = 16 - len(length)
    pad = ("0" * padsize).encode("ascii")

    # Concatenate prefix and message.
    parcel = pad + length + message

    return parcel