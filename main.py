import time
import sys

if len(sys.argv) != 2:
    print("Usage: python main.py <duration_in_seconds>")
    sys.exit(1)

duration = int(sys.argv[1])

for i in range(duration):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {current_time}")
    time.sleep(1)
