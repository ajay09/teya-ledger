from decimal import Decimal

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from .errors import (
    DuplicateModelError,
    InsufficientFundsError,
    ModelNotFoundError,
)
from .models import Account, Transaction
from .schemas import (
    AccountBalanceSchema,
    AccountCreateSchema,
    AccountSchema,
    PaginationSchema,
    TransactionCreateSchema,
    TransactionHistorySchema,
    TransactionSchema,
)

blueprint = Blueprint("ledger", __name__, url_prefix="/v1")


@blueprint.errorhandler(ModelNotFoundError)
def handle_not_found(error):
    return jsonify(error=str(error)), 404


@blueprint.errorhandler(DuplicateModelError)
def handle_duplicate(error):
    return jsonify(error=str(error)), 409


@blueprint.errorhandler(InsufficientFundsError)
def handle_insufficient_funds(error):
    return jsonify(error=str(error)), 409


@blueprint.route("/accounts")
class Accounts(MethodView):
    @blueprint.arguments(
        AccountCreateSchema,
        error_status_code=400,
        example={"account_number": "ACC-001", "currency": "GBP"},
    )
    @blueprint.response(201, AccountSchema)
    def post(self, account_data):
        return Account.create(**account_data)


@blueprint.route("/accounts/<string:account_number>")
class AccountBalance(MethodView):
    @blueprint.response(200, AccountBalanceSchema)
    def get(self, account_number: str):
        account = Account.get(account_number)
        balance = Decimal(Account.get_balance(account_number)) / 100
        return {
            "account_number": account.account_number,
            "currency": account.currency,
            "balance": f"{balance:.2f}",
        }


@blueprint.route("/accounts/<string:account_number>/transactions")
class AccountTransactions(MethodView):
    @blueprint.arguments(
        TransactionCreateSchema,
        error_status_code=400,
        example={
            "transaction_type": "deposit",
            "amount": "10.25",
            "idempotency_key": "deposit-001",
        },
    )
    @blueprint.response(201, TransactionSchema)
    def post(self, transaction_data, account_number: str):
        return Transaction.create(account_number, **transaction_data)

    @blueprint.arguments(
        PaginationSchema,
        location="query",
        error_status_code=400,
    )
    @blueprint.response(
        200,
        TransactionHistorySchema,
        example={
            "transactions": [
                {
                    "id": 1,
                    "account_number": "ACC-001",
                    "transaction_type": "deposit",
                    "amount": "10.25",
                    "idempotency_key": "deposit-001",
                    "reference": "5da9d94e-9047-49a8-b2f6-f350daf637de",
                    "transaction_timestamp": "2026-09-21T12:00:00+00:00",
                    "created_at": "2026-09-21T12:00:00+00:00",
                }
            ],
            "page": 1,
            "page_size": 20,
            "total": 1,
        },
    )
    def get(self, pagination, account_number: str):
        transactions = Transaction.list_for_account(account_number)
        page = pagination["page"]
        page_size = pagination["page_size"]
        start = (page - 1) * page_size
        return {
            "transactions": transactions[start : start + page_size],
            "page": page,
            "page_size": page_size,
            "total": len(transactions),
        }
