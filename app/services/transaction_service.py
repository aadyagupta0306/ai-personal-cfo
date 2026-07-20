from app.database.session import SessionLocal
from app.models.transaction import Transaction

def add_transaction(amount, type, category, date, account_id, description=None, payment_method=None):
    session = SessionLocal()
    try:
        txn = Transaction(
            amount=amount,
            type=type,
            category=category,
            date=date,
            account_id=account_id,
            description=description,
            payment_method=payment_method,
        )
        session.add(txn)
        session.commit()
        session.refresh(txn)
        return txn
    finally:
        session.close()

def get_all_transactions():
    session = SessionLocal()
    try:
        return session.query(Transaction).order_by(Transaction.date.desc()).all()
    finally:
        session.close()