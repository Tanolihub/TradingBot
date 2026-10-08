import dateutil.parser
import datetime
import traceback

trade_data = {"p": 150.5, "t": "2023-11-09T15:00:00.123456789Z"}
t_str = trade_data.get("t")
try:
    if t_str:
        ts = dateutil.parser.isoparse(t_str)
    else:
        ts = datetime.datetime.now(datetime.timezone.utc)
    print(ts)
except Exception as e:
    traceback.print_exc()
