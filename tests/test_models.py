import unittest

from ledger.errors import (
    DuplicateModelError,
    InsufficientFundsError,
    ModelNotFoundError,
)
from ledger.models import (
    Account,
    Transaction,
    TransactionType,
)


class InMemoryDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.account = Account.create("ACC-001", "gbp")

    def test_transactions_are_recorded(self) -> None:
        other_account = Account.create("ACC-002")
        tranx_count = len(Transaction.list_for_account(self.account.account_number))

        Transaction.create(
            self.account.account_number,
            TransactionType.DEPOSIT,
            "1000",
            "primary-deposit",
        )
        Transaction.create(
            other_account.account_number,
            TransactionType.DEPOSIT,
            "500",
            "savings-deposit",
        )

        self.assertEqual(
            len(Transaction.list_for_account(self.account.account_number)),
            tranx_count + 1,
        )
        self.assertEqual(
            len(
                Transaction.list_for_account(
                    other_account.account_number
                )
            ),
            1,
        )

    def test_account_calculates_its_balance(self) -> None:
        Transaction.create(
            self.account.account_number,
            TransactionType.DEPOSIT,
            "1000",
            "deposit",
        )
        Transaction.create(
            self.account.account_number,
            TransactionType.WITHDRAW,
            "250",
            "withdraw",
        )

        self.assertEqual(
            Account.get_balance(
                self.account.account_number
            ),
            75_000,
        )

    def test_amount_is_stored_in_pence(self) -> None:
        transaction = Transaction.create(
            self.account.account_number,
            TransactionType.DEPOSIT,
            "10.25",
            "decimal-deposit",
        )

        self.assertEqual(transaction.amount, 1_025)

    def test_idempotency_keys_are_unique(self) -> None:
        Transaction.create(
            self.account.account_number,
            TransactionType.DEPOSIT,
            "100",
            "request-1",
        )

        with self.assertRaises(DuplicateModelError):
            Transaction.create(
                self.account.account_number,
                TransactionType.DEPOSIT,
                "100",
                "request-1",
            )

    def test_withdrawal_with_insufficient_balance_is_rejected(self) -> None:
        account = Account.create("ACC-INSUFFICIENT")

        with self.assertRaises(InsufficientFundsError):
            Transaction.create(
                account.account_number,
                TransactionType.WITHDRAW,
                "100",
                "insufficient-withdrawal",
            )

        self.assertEqual(Transaction.list_for_account(account.account_number), ())


if __name__ == "__main__":
    unittest.main()
