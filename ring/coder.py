""":mod:`ring.coder` --- Auto encode/decode layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Coder is a configurable layer that how to encode raw data and how to decode
stored cache data.

Built-in coders
---------------

- :func:`ring.coder.bypass`: By-pass coder
- :class:`ring.coder.JsonCoder`: JSON coder
- Pickle coder

Create a new coder
------------------

Users can register new custom coders with aliases.

Coder types:

  - :class:`ring.coder.Coder`
  - :class:`ring.coder.CoderTuple`

Registry:

  - :data:`ring.coder.registry`
  - :class:`ring.coder.Registry`
"""
import abc
import six
from collections import namedtuple
try:
    import ujson as json_mod
except ImportError:
    import json as json_mod

try:
    import cpickle as pickle_mod
except ImportError:
    import pickle as pickle_mod


@six.add_metaclass(abc.ABCMeta)
class Coder(object):
    """Abstract coder interface.

    See :func:`coderize` to create a Coder-compatible object in easy way.
    See :class:`CoderTuple` to create a Coder-compatible object with functions.
    """

    @abc.abstractmethod
    def encode(self):  # pragma: no cover
        """Abstract encode function. Children must implement this function."""
        pass

    @abc.abstractmethod
    def decode(self):  # pragma: no cover
        """Abstract decode function. Children must implement this function."""
        pass


CoderTuple = namedtuple('Coder', ['encode', 'decode'])  #: Coder-compatible tuple with encode and decode functions
Coder.register(CoderTuple)


def coderize(raw_coder):
    if isinstance(raw_coder, Coder):
        coder = raw_coder
    else:
        if isinstance(raw_coder, str):  # py2 support
            raise TypeError(
                "The given coder is not a registered name in coder registry.")
        if isinstance(raw_coder, tuple):
            coder = CoderTuple(*raw_coder)
        elif hasattr(raw_coder, 'encode') and hasattr(raw_coder, 'decode'):
            coder = CoderTuple(raw_coder.encode, raw_coder.decode)
        else:
            raise TypeError(
                "The given coder is not a coder compatibile object or "
                "not a registered name in coder registry")
    return coder


class Registry(object):
    """Coder registry.

    :see: :func:`ring.coder.registry` for default registry instance.
    """

    __slots__ = ('coders', )

    def __init__(self):
        self.coders = {}

    def register(self, coder_name, raw_coder):
        """Register `raw_coder` as a new coder with alias `coder_name`.

        Coder can be one of next types:

          - A :class:`Coder` subclass.
          - A :class:`CoderTuple` object.
          - A tuple of encode and decode functions.
          - An object which has encode and decode methods.

        :param str coder_name: A new coder name to register.
        :param object raw_coder: A new coder object.
        """
        coder = coderize(raw_coder)
        self.coders[coder_name] = coder

    def get(self, coder_name):
        """Get the registered coder for corresponding `coder_name`.

        This method is internally called when `coder` parameter is passed to
        ring object factory.
        """
        coder = self.coders.get(coder_name)
        return coder


def bypass(x):
    """Default coder which does nothing."""
    return x


class JsonCoder(Coder):
    """JSON Coder.

    When :mod:`ujson` package is installed, `ujson` is automatically selected;
    Otherwise :mod:`json` will be used.
    """

    @staticmethod
    def encode(data):
        """Dump data to JSON string and encode it to UTF-8 bytes"""
        return json_mod.dumps(data).encode('utf-8')

    @staticmethod
    def decode(binary):
        """Decode UTF-8 bytes to JSON string and load it to object"""
        return json_mod.loads(binary.decode('utf-8'))


#: The default coder registry with pre-registered coders.
#: Built-in coders are registered by default.
#:
#: :see: :class:`ring.coder.Registry` for the class definition.
registry = Registry()
registry.register(None, (bypass, bypass))
registry.register('json', JsonCoder())
registry.register('pickle', (pickle_mod.dumps, pickle_mod.loads))
