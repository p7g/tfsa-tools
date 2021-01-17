import pytest
from tfsa import Amount


@pytest.mark.parametrize(
    "amount,as_float",
    [
        (Amount(10, 50), 10.5),
        (Amount(12, 34), 12.34),
    ],
)
def test_amount_as_float(amount, as_float):
    assert float(amount) == as_float


@pytest.mark.parametrize(
    "amount,s",
    [
        (Amount(123, 45), "$123.45"),
        (Amount(100), "$100.00"),
        (Amount(0, 1), "$0.01"),
    ],
)
def test_amount_repr(amount, s):
    assert repr(amount) == s


def test_amount_equality():
    assert Amount(123, 45) == Amount(123, 45)
    assert Amount(123, 45) != Amount(123, 46)
