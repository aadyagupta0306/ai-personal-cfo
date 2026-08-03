from app.database.session import SessionLocal
from app.models.transaction import Transaction
from app.services.recurrence_engine import match_and_advance

def add_transaction(amount, type, category, date, account_id, description=None, payment_method=None):
    session = SessionLocal()
    try:
        txn = Transaction(
            amount=amount,
            type=type,
            category=category,
            date=date,
            description=description,
            payment_method=payment_method,
            account_id=account_id,
        )
        session.add(txn)
        session.commit()
        session.refresh(txn)
    finally:
        session.close()

    match_and_advance(txn)
    return txn

def get_all_transactions():
    session = SessionLocal()
    try:
        return session.query(Transaction).order_by(Transaction.date.desc()).all()
    finally:
        session.close()