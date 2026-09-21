from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import uuid4

from .errors import DuplicateModelError, InsufficientFundsError, ModelNotFoundError


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_pence(amount: str) -> int:
    if not isinstance(amount, str):
        raise TypeError("amount must be a string")
    try:
        amount_in_pence = Decimal(amount) * 100
    except InvalidOperation as error:
        raise TypeError("amount must be a number") from error

    if amount_in_pence != amount_in_pence.to_integral_value():
        raise ValueError("amount must have no more than two decimal places")
    return int(amount_in_pence)


class TransactionType(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class InMemoryDatabase:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.transactions: dict[str, dict[int, Transaction]] = {}


db = InMemoryDatabase()


@dataclass(slots=True)
class Account:
    account_number: str
    currency: str = "GBP"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, account_number: str, currency: str = "GBP",) -> "Account":
        account_number = account_number.strip()
        if account_number in db.accounts:
            raise DuplicateModelError(f"Account {account_number!r} already exists")
        account = cls(account_number=account_number, currency=currency.upper())
        db.accounts[account_number] = account
        db.transactions[account_number] = {}
        return account

    @classmethod
    def get(cls, account_number: str,) -> "Account":
        try:
            return db.accounts[account_number]
        except KeyError as error:
            raise ModelNotFoundError(f"Account {account_number!r} does not exist") from error

    @classmethod
    def get_balance(cls, account_number: str,) -> int:
        return sum(tranx.signed_amount for tranx in Transaction.list_for_account(account_number))


@dataclass(slots=True)
class Transaction:
    account_number: str
    transaction_type: TransactionType
    amount: int
    idempotency_key: str
    reference: str = field(default_factory=lambda: str(uuid4()))
    transaction_timestamp: datetime = field(default_factory=utc_now)
    id: int | None = None
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(
            cls,
            account_number: str,
            transaction_type: TransactionType | str,
            amount: str,
            idempotency_key: str,
            *,
            reference: str | None = None,
            transaction_timestamp: datetime | None = None,
    ) -> "Transaction":
        Account.get(account_number)
        account_transactions = db.transactions[account_number]
        if any(
            tranx.idempotency_key == idempotency_key
            for tranx in account_transactions.values()
        ):
            raise DuplicateModelError(f"Transaction {idempotency_key!r} already exists")

        transaction_id = len(account_transactions) + 1
        transaction = cls(
            id=transaction_id,
            account_number=account_number,
            transaction_type=TransactionType(transaction_type),
            amount=to_pence(amount),
            idempotency_key=idempotency_key,
            reference=reference if reference is not None else str(uuid4()),
            transaction_timestamp=transaction_timestamp or utc_now(),
        )
        if (
            transaction.transaction_type is TransactionType.WITHDRAW
            and transaction.amount > Account.get_balance(account_number)
        ):
            raise InsufficientFundsError("Account has insufficient balance")

        account_transactions[transaction_id] = transaction
        return transaction

    @classmethod
    def get(cls, account_number: str, transaction_id: int,) -> "Transaction":
        Account.get(account_number)
        try:
            return db.transactions[account_number][transaction_id]
        except KeyError as error:
            raise ModelNotFoundError(f"Transaction {transaction_id} does not exist") from error

    @classmethod
    def list_for_account(cls, account_number: str,) -> tuple["Transaction", ...]:
        Account.get(account_number)
        return tuple(db.transactions[account_number].values())

    def __post_init__(self) -> None:
        if not self.account_number.strip():
            raise ValueError("account_number must not be empty")
        if not isinstance(self.amount, int) or isinstance(self.amount, bool):
            raise TypeError("amount must be an integer")
        if self.amount <= 0:
            raise ValueError("amount must be greater than zero")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")

        transaction_type = TransactionType(self.transaction_type)
        self.transaction_type = transaction_type

    @property
    def signed_amount(self) -> int:
        if self.transaction_type is TransactionType.DEPOSIT:
            return self.amount
        return -self.amount
