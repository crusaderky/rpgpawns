import importlib.metadata

from rpgpawns.pawn import make_collage, make_pawn

try:
    __version__ = importlib.metadata.version("rpgpawns")
except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    # Local copy, not installed with pip
    __version__ = "9999"


__all__ = ("__version__", "make_collage", "make_pawn")
