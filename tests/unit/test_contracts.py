from uuid import uuid4

import pytest
from pydantic import ValidationError

from mercury_rec.contracts import UserEventV1


def test_user_event_accepts_canonical_payload() -> None:
    event = UserEventV1.model_validate(
        {
            "event_id": str(uuid4()),
            "user_id": "user-123",
            "item_id": "item-892",
            "event_type": "purchase",
            "event_time": "2026-01-15T09:41:00Z",
            "price": "29.99",
            "currency": "EUR",
            "source": "hm-replay",
        }
    )

    assert event.schema_version == 1
    assert str(event.price) == "29.99"


def test_user_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        UserEventV1.model_validate(
            {
                "event_id": str(uuid4()),
                "user_id": "user-123",
                "item_id": "item-892",
                "event_type": "purchase",
                "event_time": "2026-01-15T09:41:00Z",
                "price": "29.99",
                "currency": "EUR",
                "source": "hm-replay",
                "price_unit": "cents",
            }
        )
