import pytest
from ratelimiter import TokenBucket


def test_starts_full_and_spends_exact_capacity():
    b = TokenBucket(capacity=3, refill_per_sec=0)
    assert [b.allow(0) for _ in range(4)] == [True, True, True, False]


def test_refill_never_exceeds_capacity():
    b = TokenBucket(capacity=2, refill_per_sec=1)
    b.allow(0); b.allow(0)
    assert b.allow(100) and b.allow(100)
    assert not b.allow(100)


def test_rejects_bad_settings():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_per_sec=1)
