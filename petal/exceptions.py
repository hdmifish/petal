"""Petal Exception module"""


class CommandError(Exception):
    """Raised when a Command is given bad input."""
    pass


class TunnelSetupError(Exception):
    """Raised when a Tunnel fails to be established."""
    pass
