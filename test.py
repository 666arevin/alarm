import threading
import time

th = threading.Thread(target=input, daemon=True)
th.start()
print(th.is_alive())
print("Дальше")

time.sleep(2)


