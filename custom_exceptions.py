class W2GError(Exception):
    """Base class for all W2G errors."""
    pass

class AccessDeniedError(W2GError):
    """Raised when an action is forbidden with the specified credentials. (403)"""
    pass

class NotFoundError(W2GError):
    """Raised when an action at the specified URL cannot be found. (404)"""
    pass