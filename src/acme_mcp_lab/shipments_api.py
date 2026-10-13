"""Mock Acme Logistics shipments API.

This stands in for the client's real system (for example a TMS behind a REST
API) so the lab runs offline. At a real client, replace the bodies of these
functions with calls to their API and leave server.py unchanged.
"""
import copy
import datetime
import json

_SEED = {
    "S-101": {"id": "S-101", "customer": "ACME-UK", "status": "in_transit",
              "origin": "Rotterdam", "destination": "New York", "eta": "2026-10-20"},
    "S-104": {"id": "S-104", "customer": "ACME-UK", "status": "delayed",
              "origin": "Hamburg", "destination": "Chicago", "eta": "2026-10-24", "days_late": 3},
    "S-221": {"id": "S-221", "customer": "GLOBEX", "status": "delayed",
              "origin": "Shanghai", "destination": "Dubai", "eta": "2026-10-19", "days_late": 1},
    "S-305": {"id": "S-305", "customer": "GLOBEX", "status": "delivered",
              "origin": "Antwerp", "destination": "Boston", "eta": "2026-10-02"},
}
_SHIPMENTS = copy.deepcopy(_SEED)


def reset() -> None:
    """Restore the sample data (used by the tests)."""
    _SHIPMENTS.clear()
    _SHIPMENTS.update(copy.deepcopy(_SEED))


def search(status: str, customer: str | None = None) -> list[dict]:
    """Short summary of every shipment with this status (and customer, if given)."""
    return [
        {"id": s["id"], "customer": s["customer"], "eta": s["eta"]}
        for s in _SHIPMENTS.values()
        if s["status"] == status and (customer is None or s["customer"] == customer)
    ]


def get(shipment_id: str) -> dict:
    """Full record for one shipment. Raises ValueError for an unknown ID."""
    if shipment_id not in _SHIPMENTS:
        raise ValueError(f"No shipment with ID {shipment_id}. IDs look like S-104.")
    return dict(_SHIPMENTS[shipment_id])


def get_json(shipment_id: str) -> str:
    """Full record for one shipment, as a JSON string."""
    return json.dumps(get(shipment_id), indent=2)


def check_eta(new_eta: str) -> None:
    """Raise ValueError unless new_eta is a YYYY-MM-DD date."""
    try:
        datetime.date.fromisoformat(new_eta)
    except ValueError:
        raise ValueError(f"new_eta must be a date in YYYY-MM-DD format, got {new_eta!r}.")


def update_eta(shipment_id: str, new_eta: str) -> dict:
    """Change a shipment's ETA and return the updated record."""
    get(shipment_id)
    check_eta(new_eta)
    _SHIPMENTS[shipment_id]["eta"] = new_eta
    return get(shipment_id)
