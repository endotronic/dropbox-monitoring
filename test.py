import sys
from time import sleep

n = 1000

while True:
    print("Syncing {} files".format(n))
    print("Downloading {} files".format(n))
    sys.stdout.flush()
    sleep(3)

    if n > 5:
        n -= 5
