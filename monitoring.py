import re
import signal
import sys
from threading import Thread

from prometheus_client import start_http_server, Gauge  # type: ignore

up_to_date_gauge = Gauge(
    "dropbox_is_up_to_date",
    "1 if up to date, 0 if syncing",
)

num_syncing_gauge = Gauge(
    "dropbox_num_syncing",
    "Number of files currently syncing",
)

num_downloading_gauge = Gauge(
    "dropbox_num_downloading",
    "Number of files currently downloading",
)

num_uploading_gauge = Gauge(
    "dropbox_num_uploading",
    "Number of files currently uploading",
)


class DropboxMonitor:
    """
    Observed messages from `dropbox status`

    Up to date
    Syncing...
    Syncing 176 files • 6 secs
    Downloading 176 files (6 secs)
    """

    def __init__(self) -> None:
        self.status_matcher = re.compile("(Syncing|Downloading|Uploading) (\\d+) files")

    def start(self):
        start_http_server(8000)
        print("MONITORING: Started Prometheus server on port 8000")

        # Start a thread to process events. This is a "quick and dirty"
        # way to handle when a status is _not_ reported, e.g. to change
        # the value of the upload gauge when upload is no longer reported.
        self.thread = Thread(target=self.thread_proc, daemon=True)

    def process_line(self, line: str) -> None:
        try:
            status_match = self.status_matcher.match(line)
            if status_match:
                action, num_files_str = status_match.groups()
                num_files = int(num_files_str)
                if action == "Syncing":
                    num_syncing_gauge.set(num_files)
            elif line != "Syncing...":
                raise Exception()
        except:
            sys.stderr.write("MONITORING: Cannot parse '{}'\n".format(line))

    def thread_proc(self):
        pass


class ExitException(Exception):
    @classmethod
    def raise_for_exit(cls, *args):
        raise cls()


if __name__ == "__main__":
    monitor = DropboxMonitor()
    monitor.start()

    # Raise an exception when receiving a signal to terminate
    signal.signal(signal.SIGHUP, ExitException.raise_for_exit)
    signal.signal(signal.SIGINT, ExitException.raise_for_exit)
    signal.signal(signal.SIGTERM, ExitException.raise_for_exit)

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                # This is an expected exit condition
                break

            # Echo to stdout and process the line
            sys.stdout.write(line)
            sys.stdout.flush()
            monitor.process_line(line.strip())
    except ExitException:
        print("MONITORING: Stopped gracefully")
        pass
