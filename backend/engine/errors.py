"""Typed errors for NetArchitect. API layer maps these to HTTP 422 via to_dict()."""

from typing import Any


class NetArchError(Exception):
    """Base for every engine error. Carries a message plus structured details."""

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {"type": type(self).__name__, "message": self.message, "details": self.details}


class PhysicalDistanceViolationError(NetArchError):
    """Requested media cannot cover the link distance (e.g. copper > 100 m)."""


class AddressSpaceExhaustedError(NetArchError):
    """Root prefix too small for the requested subnets."""


class InvalidPrefixError(NetArchError):
    """Malformed CIDR or host bits set in a network prefix."""


class InvalidParameterError(NetArchError):
    """Any other invalid design input."""


class TopologyError(NetArchError):
    """Topology cannot be built (disconnected sites, unknown endpoints, ...)."""
