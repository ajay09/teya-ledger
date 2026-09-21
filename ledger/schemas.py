from marshmallow import Schema, fields, validate


class PenceAsString(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        pounds, pence = divmod(value, 100)
        return f"{pounds}.{pence:02d}"


class AccountCreateSchema(Schema):
    account_number = fields.String(required=True)
    currency = fields.String(load_default="GBP", validate=validate.Length(equal=3))


class AccountSchema(Schema):
    account_number = fields.String(required=True)
    currency = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class AccountBalanceSchema(Schema):
    account_number = fields.String(required=True)
    currency = fields.String(required=True)
    balance = fields.String(required=True)


class TransactionCreateSchema(Schema):
    transaction_type = fields.String(required=True, validate=validate.OneOf(["deposit", "withdraw"]))
    amount = fields.String(required=True,validate=validate.Regexp(r"^\d+(\.\d{1,2})?$"))
    idempotency_key = fields.String(required=True)


class TransactionSchema(Schema):
    id = fields.Integer(required=True)
    account_number = fields.String(required=True)
    transaction_type = fields.String(required=True)
    amount = PenceAsString(required=True)
    idempotency_key = fields.String(required=True)
    reference = fields.String(required=True)
    transaction_timestamp = fields.DateTime(required=True)
    created_at = fields.DateTime(required=True)


class PaginationSchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )


class TransactionHistorySchema(Schema):
    transactions = fields.List(fields.Nested(TransactionSchema), required=True)
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    total = fields.Integer(required=True)
