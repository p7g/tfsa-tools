# tfsa

Some utilities to try and make it easier to keep your own TFSA records. Read
[LICENSE][1] before using.

[1]: https://github.com/p7g/tfsa-tools/blob/master/LICENSE

To use this:
1. Go to the CRA website and open the TFSA transaction summary (include all
   years).
2. Audit the [scraping script][2] yourself, and then run it in the console.
3. Copy the JSON output and save it somewhere.
4. See API documentation below.

[2]: https://github.com/p7g/tfsa-tools/blob/master/scrape-transaction-summary.js

## API

### `Amount`

A class to represent an amount of money. Dollars and cents are stored together
as an integer to (try to) avoid the imprecision of floating point values.

#### `Amount.__init__(self, dollars=0, cents=0)`

Self-explanatary.

#### `Amount.__add__(self, other: Union[Literal[0], Amount])`

Add two amounts together. It also handles an `other` value of 0 so that you can
pass an iterable of `Amount` objects to `sum`.

#### `Amount.__sub__(self, other: Amount)`

Self-explanatary.

#### `Amount.__repr__(self)`

Get a text representation of the `Amount`, like `$123.45`.

#### `Amount.from_json(cls, dct)`

Create an `Amount` instance from a dictionary like `{"dollars": 0, "cents": 0}`.
### `Transaction`

This is a class to store one entry of CRA's transaction summary. It has an
attribute for the `date`, the `type` (`"contribution"` or `"withdrawal"`), and
the `amount`.

There is a `from_json` classmethod to create an instance from a dictionary.

### `TransactionSummary`

This class represents the summation of a sequence of `Transaction` objects. It
has a `contributions` attribute and a `withdrawals` attribute, both of which are
`Amount` objects, and represent the summation of all `Transaction` objects of
their respective types.

#### `TransactionHistory`

Objects of this type represent CRA's transaction summary. There is a
`transactions` attribute, which is a list of `Transaction` objects.

#### `TransactionHistory.contributions`

A list of `Amount` objects for all the `Transaction` objects that are
contributions.

#### `TransactionHistory.withdrawals`

A list of `Amount` objects for all the `Transaction` objects that are
withdrawals.

### `TFSA`

This class represents a TFSA I guess. It stores a date of birth and a
`TransactionHistory` object, and implements several useful calculations.

#### `TFSA.__init__(self, date_of_birth, transaction_history)`

Make a new TFSA object. `date_of_birth` should be a string suitable for passing
to `date.fromisoformat` and `transaction_history` should be a
`TransactionHistory` object.

#### `TFSA.dollar_limit_for_year(year)`

Given a year greater than or equal to 2009 and less than or equal to 2021, gets
the dollar limit for that year.

#### `TFSA.yearly_gross_contribution_room(self)`

Returns tuples of `(year, dollar_limit)` for each year where the user had some
contribution room (i.e. from the year they turned 18 or from 2009, which ever is
greater).

#### `TFSA.total_gross_contribution_room(self)`

The sum of the dollar limits returned by `yearly_gross_contribution_room`.

#### `TFSA.contribution_room(self, year)`

Given a year, returns the net amount of contribution room as of the beginning of
that year. This calculation is based on the provided `TransactionHistory` and
the user's date of birth.

## Example

Let's say you wanted to calculate what percentage of your total gross
contribution room is currently in use. You could do this:

```python
from tfsa import TFSA, TransactionHistory

date_of_birth = '1978-03-23'  # string understood by date.fromisoformat
history_json = []  # retrieved by scraping script

history = TransactionHistory.from_json(history_json)
tfsa = TFSA(date_of_birth, history)

gross_contribution_room = tfsa.total_gross_contribution_room()
net_contributed = sum(history.contributions) - sum(history.withdrawals)
print("%.2f%%" % (100 * net_contributed / gross_contribution_room))
```
