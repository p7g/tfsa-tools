from __future__ import annotations

import datetime
import decimal

if False:
    import typing

    TransactionType = typing.Literal["contribution", "withdrawal"]

    class AmountJSON(typing.TypedDict):
        cents: int
        dollars: int

    class TransactionJSON(typing.TypedDict):
        date: str
        type: TransactionType
        amount: AmountJSON


class Amount:
    def __init__(self, dollars: int = 0, cents: int = 0):
        self.total_cents = dollars * 100 + cents

    def __float__(self) -> float:
        return (self.total_cents // 100) + (self.total_cents % 100 / 100)

    def __int__(self) -> int:
        return self.total_cents

    def __add__(self, other) -> Amount:
        if other == 0:
            return self
        if isinstance(other, Amount):
            return Amount(cents=self.total_cents + other.total_cents)
        return NotImplemented

    def __sub__(self, other) -> Amount:
        if isinstance(other, Amount):
            return Amount(cents=self.total_cents - other.total_cents)
        return NotImplemented

    def __mul__(self, other) -> Amount:
        if not isinstance(other, (int, Amount)):
            return NotImplemented
        return Amount(cents=self.total_cents * int(other))

    def __div__(self, other) -> Amount:
        if not isinstance(other, (int, Amount)):
            return NotImplemented
        return Amount.from_float(self.total_cents / int(other))

    def __rdiv__(self, other) -> Amount:
        if not isinstance(other, (int, Amount)):
            return NotImplemented
        return Amount.from_float(int(other) / self.total_cents)

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __floordiv__ = __truediv__ = __div__
    __rfloordiv__ = __rtruediv__ = __rdiv__

    def __repr__(self) -> str:
        return "$%0.2f" % float(self)

    def __eq__(self, other: Amount):
        if not isinstance(other, Amount):
            return NotImplemented
        return self.total_cents == other.total_cents

    @classmethod
    def from_json(cls, dct: AmountJSON) -> Amount:
        return cls(dct["dollars"], dct["cents"])

    @classmethod
    def from_float(cls, flt: float) -> Amount:
        dec = decimal.Decimal(flt).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )
        dollars, cents = dec // 1, dec % 1
        return cls(int(dollars), int(cents * 100))


class Transaction:
    def __init__(
        self, date: datetime.date, type: TransactionType, amount: Amount
    ) -> None:
        self.date = date
        self.type = type
        self.amount = amount

    @classmethod
    def from_json(cls, dct: TransactionJSON) -> Transaction:
        return cls(
            date=datetime.date.fromisoformat(dct["date"]),
            type=dct["type"],
            amount=Amount.from_json(dct["amount"]),
        )


class TransactionSummary:
    def __init__(
        self, contributions: Amount = None, withdrawals: Amount = None
    ) -> None:
        self.contributions = contributions or Amount()
        self.withdrawals = withdrawals or Amount()

    def __iadd__(self, transaction) -> TransactionSummary:
        if not isinstance(transaction, Transaction):
            return NotImplemented
        if transaction.type == "contribution":
            self.contributions += transaction.amount
        else:
            self.withdrawals += transaction.amount
        return self


class TransactionHistory:
    def __init__(self, transactions: typing.Sequence[Transaction]) -> None:
        self.transactions = list(sorted(transactions, key=lambda t: t.date))

    def year_summary(self, year: int) -> TransactionSummary:
        summary = TransactionSummary()
        for tr in self.transactions:
            if tr.date.year == year:
                summary += tr
        return summary

    def _filter(
        self, type: TransactionType
    ) -> typing.Generator[Transaction, None, None]:
        return (tr for tr in self.transactions if tr.type == type)

    @property
    def contributions(self) -> list[Amount]:
        return [tr.amount for tr in self._filter("contribution")]

    @property
    def withdrawals(self) -> list[Amount]:
        return [tr.amount for tr in self._filter("withdrawal")]

    @classmethod
    def from_json(cls, dcts: list[TransactionJSON]) -> TransactionHistory:
        return cls([Transaction.from_json(d) for d in dcts])


class TFSA:
    def __init__(
        self, date_of_birth: datetime.date, transaction_history: TransactionHistory
    ) -> None:
        self._dob = date_of_birth
        self._hist = transaction_history

    @property
    def _first_year(self) -> int:
        return max(self._dob.year + 18, 2009)

    @staticmethod
    def dollar_limit_for_year(year) -> Amount:
        if 2009 <= year <= 2012:
            return Amount(5_000)
        if 2013 <= year <= 2014:
            return Amount(5_500)
        if year == 2015:
            return Amount(10_000)
        if 2016 <= year <= 2018:
            return Amount(5_500)
        if 2019 <= year <= 2022:
            return Amount(6_000)
        raise NotImplementedError(year)

    def yearly_gross_contribution_room(self) -> list[tuple[int, Amount]]:
        return [
            (year, self.dollar_limit_for_year(year))
            for year in range(self._first_year, datetime.datetime.now().year + 1)
        ]

    def total_gross_contribution_room(self) -> Amount:
        return sum(
            (amount for _year, amount in self.yearly_gross_contribution_room()),
            Amount(),
        )

    def contribution_room(self, year: int) -> Amount:
        last_year_net = Amount()
        if year > self._first_year:
            last_year_transactions = self._hist.year_summary(year - 1)
            last_year_room = (
                self.contribution_room(year - 1) - last_year_transactions.contributions
            )
            last_year_net = last_year_room + last_year_transactions.withdrawals
        dollar_limit = self.dollar_limit_for_year(year)
        return dollar_limit + last_year_net
