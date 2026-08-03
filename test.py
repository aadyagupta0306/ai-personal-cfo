from datetime import datetime, timedelta
import app.models.account
import app.models.goal
import app.models.budget
import app.models.expected_transaction

from app.services.expected_transaction_service import add_expected_transaction
from app.services.transaction_service import add_transaction

add_expected_transaction(
    "Test Recurring Bill", "expense", "Subscriptions", 199,
    datetime.now() - timedelta(days=3), is_recurring="monthly"
)

txn = add_transaction(
    amount=199, type="expense", category="Subscriptions",
    date=datetime.now(), account_id=1,
    description="test recurring match", payment_method="UPI"
)

print("Transaction added:", txn.id)