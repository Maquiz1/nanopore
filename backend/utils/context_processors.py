# utils/context_processors.py
from utils.access import AccessFlags


def access(request):
    """Exposes {{ access }} (see utils.access.AccessFlags) to every template."""
    return {"access": AccessFlags(request.user)}
