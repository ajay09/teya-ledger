import unittest
from decimal import Decimal

from ledger import create_app
from ledger.models import Account


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = create_app().test_client()
        cls.account_number = "API-001"
        cls.account_response = cls.client.post(
            "/v1/accounts",
            json={"account_number": cls.account_number, "currency": "GBP"},
        )

    def test_deposit_is_recorded(self) -> None:
        response = self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "deposit",
                "amount": "1000",
                "idempotency_key": "api-deposit",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["amount"], "1000.00")

    def test_balance_includes_deposits_and_withdrawals(self) -> None:
        balance = Decimal(
            self.client.get(
                f"/v1/accounts/{self.account_number}"
            ).get_json()["balance"]
        )

        self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "deposit",
                "amount": "1000",
                "idempotency_key": "api-balance-deposit",
            },
        )
        self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "withdraw",
                "amount": "250",
                "idempotency_key": "api-balance-withdraw",
            },
        )

        response = self.client.get(f"/v1/accounts/{self.account_number}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["balance"],
            f"{balance + Decimal('750.00'):.2f}",
        )

    def test_idempotent_retry_returns_the_original_transaction(self) -> None:
        payload = {
            "transaction_type": "deposit",
            "amount": "100",
            "idempotency_key": "api-duplicate",
        }
        original_response = self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json=payload,
        )

        retry_response = self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json=payload,
        )

        self.assertEqual(retry_response.status_code, 201)
        self.assertEqual(retry_response.get_json(), original_response.get_json())

    def test_idempotency_key_cannot_be_reused_with_different_data(self) -> None:
        idempotency_key = "api-duplicate-different-data"
        self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "deposit",
                "amount": "100",
                "idempotency_key": idempotency_key,
            },
        )

        response = self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "deposit",
                "amount": "200",
                "idempotency_key": idempotency_key,
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_numeric_amount_is_rejected(self) -> None:
        response = self.client.post(
            f"/v1/accounts/{self.account_number}/transactions",
            json={
                "transaction_type": "deposit",
                "amount": 100,
                "idempotency_key": "api-numeric-amount",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.get_json()["errors"]["json"])

    def test_withdrawal_with_insufficient_balance_is_rejected(self) -> None:
        account_number = "API-INSUFFICIENT"
        self.client.post(
            "/v1/accounts",
            json={"account_number": account_number, "currency": "GBP"},
        )

        response = self.client.post(
            f"/v1/accounts/{account_number}/transactions",
            json={
                "transaction_type": "withdraw",
                "amount": "100",
                "idempotency_key": "api-insufficient-withdrawal",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.get_json()["error"],
            "Account has insufficient balance",
        )

    def test_unknown_account_is_not_found(self) -> None:
        response = self.client.get("/v1/accounts/UNKNOWN")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
