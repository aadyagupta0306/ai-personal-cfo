from app.database.session import SessionLocal
from app.models.account import Account
from app.models.transaction import Transaction
from sqlalchemy import func

def add_account(name, account_type, opening_balance=0.0):
    session = SessionLocal()
    try:
        acc = Account(name=name, account_type=account_type, opening_balance=opening_balance)
        session.add(acc)
        session.commit()
        session.refresh(acc)
        return acc
    finally:
        session.close()

def get_all_accounts():
    session = SessionLocal()
    try:
        return session.query(Account).all()
    finally:
        session.close()

def get_account_balance(account_id):
    session = SessionLocal()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        txn_sum = session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account_id,
            Transaction.type == "income"
        ).scalar() or 0
        txn_sum -= session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account_id,
            Transaction.type == "expense"
        ).scalar() or 0
        return account.opening_balance + txn_sum
    finally:
        session.close()