# Teya Ledger

A small Flask API for creating accounts, recording deposits and withdrawals,
checking balances, and viewing transaction history.

## Requirements

- Python 3.11 or newer


## Run locally

Start the Flask development server with automatic reload:

```bash
python app.py
```

- Swagger UI: `http://127.0.0.1:8080/docs`

## Tests

```bash
python -m unittest discover -s tests -v
```

## Assumptions

- Request amounts are decimal strings with at most two decimal places.
- Money is stored and calculated as integer pence. API amounts and balances are
  returned as decimal strings.
- Each account has one currency. The default currency is `GBP`.
- Idempotency keys are unique within an account. Repeating the same request
  returns the original transaction, while reusing a key with different
  transaction data is rejected.
- Transactions are returned in the order they were recorded.
- Withdrawals cannot make an account balance negative.
- Data is stored in memory and is lost when the application stops.
- Authentication, authorization, logging, monitoring, and atomic operations are
  outside the scope of this exercise.
- Since atomic ops were out of scope, so I have not serialized access to the critical section where a withdrawal transaction checks the balance and then creates a transaction entry if balance is greater than the transaction amount. This is the check-then-act race condition where if multiple threads operate on the same section then they can read the same balance value and proceed with saving their transactions. This can lead to lost accout balance becoming negative. A solution would be to serialize the access to this critical section using a lock (one lock per account) so that only one thread can operate at a time and all other threads should wait thus each will see the latest balance.
- Since this is a simple ledger we can calculate the balance everytime using the ledger transactions. But in prod we can have a cached balance for faster reads, which could be atomically updated whenever a transaction is added to an account.
- For pagination, I have only implemented page based pagination, and always return starting from the first transaction. This can be extended to cursor based pagination with the option to reverse the order of results. Also for the reverse order Cursor based pagination would be a better choice as transactions are being added while someone is browsing the transaction history and a new transaction should not change the paginated result. A cursor based pagination would ensure we always return the last 20 (page size) from a fixed identifier in the table. 
