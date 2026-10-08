import datetime
trade_data = {"p": 150.5, "t": "2023-11-09T15:00:00.123456Z"}
t_str = trade_data.get("t")
ts = datetime.datetime.fromisoformat(t_str.replace('Z', '+00:00'))
print(ts)
