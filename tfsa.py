from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Amount:
    _amount: int

    def __init__(self, dollars=0, cents=0):
        self._amount = dollars * 100 + cents

    def __float__(self):
        return (self._amount // 100) + (self._amount % 100 / 100)

    def __add__(self, other):
        if other == 0:
            return self
        if isinstance(other, Amount):
            return Amount(cents=self._amount + other._amount)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Amount):
            return Amount(cents=self._amount - other._amount)
        return NotImplemented

    @staticmethod
    def _other_as_int(other):
        if isinstance(other, Amount):
            return other._amount
        if isinstance(other, int):
            return other
        return NotImplemented

    def __mul__(self, other):
        other = self._other_as_int(other)
        if other is NotImplemented:
            return NotImplemented
        return Amount(cents=self._amount * other)

    def __div__(self, other):
        other = self._other_as_int(other)
        if other is NotImplemented:
            return NotImplemented
        return Amount.from_float(self._amount / other)

    def __rdiv__(self, other):
        other = self._other_as_int(other)
        if other is NotImplemented:
            return NotImplemented
        return Amount.from_float(other / self._amount)

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __floordiv__ = __truediv__ = __div__
    __rfloordiv__ = __rtruediv__ = __rdiv__

    def __repr__(self):
        return "$%0.2f" % float(self)

    @classmethod
    def from_json(cls, dct):
        return cls(dct["dollars"], dct["cents"])

    @classmethod
    def from_float(cls, flt):
        dollars, cents = flt // 1, flt % 1
        return cls(dollars, cents)


@dataclass
class Transaction:
    date: date
    type: str
    amount: Amount

    @classmethod
    def from_json(cls, dct):
        return cls(
            date=date.fromisoformat(dct["date"]),
            type=dct["type"],
            amount=Amount.from_json(dct["amount"]),
        )


@dataclass
class TransactionSummary:
    contributions: Amount = field(default_factory=Amount)
    withdrawals: Amount = field(default_factory=Amount)

    def __iadd__(self, transaction):
        if not isinstance(transaction, Transaction):
            return NotImplemented
        if transaction.type == "contribution":
            self.contributions += transaction.amount
        else:
            self.withdrawals += transaction.amount
        return self


class TransactionHistory:
    def __init__(self, transactions):
        self.transactions = list(sorted(transactions, key=lambda t: t.date))

    def year_summary(self, year):
        summary = TransactionSummary()
        for tr in self.transactions:
            if tr.date.year == year:
                summary += tr
        return summary

    def _filter(self, type):
        return (tr for tr in self.transactions if tr.type == type)

    @property
    def contributions(self):
        return [tr.amount for tr in self._filter("contribution")]

    @property
    def withdrawals(self):
        return [tr.amount for tr in self._filter("withdrawal")]

    @classmethod
    def from_json(cls, dcts):
        return cls([Transaction.from_json(d) for d in dcts])


class TFSA:
    def __init__(self, date_of_birth, transaction_history):
        self._dob = date.fromisoformat(date_of_birth)
        self._hist = transaction_history

    @property
    def _first_year(self):
        return max(self._dob.year + 18, 2009)

    @staticmethod
    def dollar_limit_for_year(year):
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

    def yearly_gross_contribution_room(self):
        return [
            (year, self.dollar_limit_for_year(year))
            for year in range(self._first_year, datetime.now().year + 1)
        ]

    def total_gross_contribution_room(self):
        return sum(amount for _year, amount in self.yearly_gross_contribution_room())

    def contribution_room(self, year):
        last_year_net = Amount()
        if year > self._first_year:
            last_year_transactions = self._hist.year_summary(year - 1)
            last_year_room = (
                self.contribution_room(year - 1) - last_year_transactions.contributions
            )
            last_year_net = last_year_room + last_year_transactions.withdrawals
        dollar_limit = self.dollar_limit_for_year(year)
        return dollar_limit + last_year_net
