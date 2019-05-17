"""Petal Exception module"""


class CommandArgsError(Exception):
    """Raised when a Command is invoked with malformed arguments."""
    pass


class CommandAuthError(Exception):
    """Raised when a Command is invoked with insufficient permissions."""
    pass


class CommandInputError(Exception):
    """Raised when a Command is given bad input."""
    pass


class CommandOperationError(Exception):
    """Raised when a Command fails, but NOT due to bad input."""
    pass


class TunnelHobbled(Exception):
    """Raised when a Tunnel is unable to comply with an order. Should always
        be passed details about what the Tunnel cannot do.
    """
    # 13. (1) By commanding the army to advance or to retreat, being ignorant
    #   of the fact that it cannot obey. This is called hobbling the army.
    #         ~ Sun Tzu, the Art of War :: III. Attack by Stratagem ~
    pass


class TunnelSetupError(Exception):
    """Raised when a Tunnel fails to be established."""
    pass
