from app.ai.transaction_parser import parse_transaction

result = parse_transaction("spent 500 on swiggy yesterday")
print(result)

result2 = parse_transaction("got 15000 from my internship on the 15th")
print(result2)