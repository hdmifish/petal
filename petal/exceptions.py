"""Petal Exception module"""


class CommandArgsError(Exception):
    """Raised when a Command is invoked with malformed arguments.
        Raising this Exception will allow the user to rerun the command by
        editing their message. Therefore it should NOT be raised if any concrete
        changes have been made by the Command already.
    """
    pass


class CommandAuthError(Exception):
    """Raised when a Command is invoked with insufficient permissions.
        Raising this Exception will NOT allow the user to rerun the command by
        editing. It should be safe to raise no matter how far in the Command is.
    """
    pass


class CommandExit(Exception):
    """Raised when a Command wants to stop IMMEDIATELY, for whatever reason.
        Raising this Exception will NOT allow the user to rerun the command by
        editing. It should be safe to raise no matter how far in the Command is.
    """
    pass


class CommandInputError(Exception):
    """Raised when a Command is given bad input.
        Raising this Exception will allow the user to rerun the command by
        editing their message. Therefore it should NOT be raised if any concrete
        changes have been made by the Command already.
    """
    pass


class CommandOperationError(Exception):
    """Raised when a Command fails, but NOT due to bad input.
        Raising this Exception will NOT allow the user to rerun the command by
        editing. It should be safe to raise no matter how far in the Command is.
    """
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
