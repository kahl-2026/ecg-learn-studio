"""API module - JSON RPC server for TUI communication."""

from .handlers import RequestHandler

__all__ = ["ECGLearnAPIServer", "RequestHandler"]


def __getattr__(name: str):
    # Avoid importing server at package import time so `python -m ecg_learn.api.server`
    # does not trigger runpy's "found in sys.modules prior to execution" warning.
    if name == "ECGLearnAPIServer":
        from .server import ECGLearnAPIServer

        return ECGLearnAPIServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
