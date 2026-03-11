import importlib.metadata

# Import implementation modules
from rpgpawns.helloworld import hello

try:
    __version__ = importlib.metadata.version("rpgpawns")
except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    # Local copy, not installed with pip
    __version__ = "9999"


__all__ = ("__version__", "hello")
