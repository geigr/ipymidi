import importlib.metadata

from ipymidi.event import Listener
from ipymidi.interface import get_interface

try:
    __version__ = importlib.metadata.version("ipymidi")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


__all__ = ["Listener", "get_interface"]
