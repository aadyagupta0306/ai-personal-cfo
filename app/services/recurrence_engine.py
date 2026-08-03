from datetime import timedelta
from dateutil.relativedelta import relativedelta
from app.database.session import SessionLocal
from app.models.expected_transaction import ExpectedTransaction

AMOUNT_TOLERANCE = 0.15   # 15% either side counts as a match
DATE_WINDOW_DAYS = 10     # transaction within +/- 10 days of expected date counts as a match

def _next_date(current_date, recurrence):
    if recurrence == "monthly":
        return current_date + relativedelta(months=1)
    if recurrence == "weekly":
        return current_date + timedelta(weeks=1)
    return None

def match_and_advance(transaction):
    """
    Called right after a real transaction is saved.
    Looks for a pending ExpectedTransaction it fulfills; if found,
    marks it fulfilled and, if recurring, creates the next cycle.
    """
    session = SessionLocal()
    try:
        candidates = session.query(ExpectedTransaction).filter(
            ExpectedTransaction.status == "pending",
            ExpectedTransaction.type == transaction.type,
            ExpectedTransaction.category == transaction.category,
        ).all()

        best_match = None
        for item in candidates:
            amount_diff = abs(item.amount - transaction.amount) / item.amount if item.amount else 1
            date_diff = abs((item.expected_date.date() - transaction.date.date()).days)

            if amount_diff <= AMOUNT_TOLERANCE and date_diff <= DATE_WINDOW_DAYS:
                if item.account_id is None or item.account_id == transaction.account_id:
                    best_match = item
                    break

        if not best_match:
            return None

        best_match.status = "received" if best_match.type == "income" else "paid"
        best_match.fulfilled_transaction_id = transaction.id

        if best_match.is_recurring in ("monthly", "weekly"):
            next_date = _next_date(best_match.expected_date, best_match.is_recurring)
            next_item = ExpectedTransaction(
                label=best_match.label,
                type=best_match.type,
                category=best_match.category,
                amount=best_match.amount,
                expected_date=next_date,
                status="pending",
                is_recurring=best_match.is_recurring,
                linked_goal_id=best_match.linked_goal_id,
                account_id=best_match.account_id,
            )
            session.add(next_item)

        session.commit()
        return best_match
    finally:
        session.close()