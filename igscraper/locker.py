import logging
import random
import time
from pathlib import Path

import portalocker

from utils import constants

logger = logging.getLogger(__name__)


class Locker:
    """Control speed and avoid to be banned officially for scraping instagram content"""

    def __init__(self):
        self._lock_path = ".interval.lock"
        self.lock_file = None
        self.last_request_time = None
        self.total_request_count = None

        # check .lock file if exists
        self.init_lock()

    def __enter__(self):
        try:
            self.lock_file = portalocker.Lock(self._lock_path, timeout=1, mode="r+")
            self.lock_file.acquire()
            logger.debug("Acquired file !")

            contents = self.lock_file.fh.readlines()
            if len(contents) == 0:
                self.last_request_time = 0
                self.total_request_count = 0

            elif len(contents) == 2:
                self.last_request_time, self.total_request_count = map(
                    lambda x: int(x), contents
                )

            else:
                raise ValueError

        except portalocker.exceptions.LockException:
            logger.warning("File already locked by other process")
        except ValueError:
            logger.error(f"There're two more lines in {self._lock_path}")

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._rewrite_records()
        self.lock_file.release()
        logger.debug("Released file !")

    def init_lock(self):
        lock = Path(self._lock_path)
        if not lock.exists():
            lock.touch()

    def _rewrite_records(self):
        self.lock_file.fh.seek(0)
        self.lock_file.fh.truncate()
        self.lock_file.fh.write(f"{self.last_request_time}\n{self.total_request_count}")

    def lock_sleep(self, *args, **kwargs):
        """Determine sleep time between current time and constrained time"""

        dt_now = int(time.time())  # round to second
        request_interval = dt_now - self.last_request_time
        sleep_time = self.sleep_time
        long_sleep_time = self.long_sleep_time

        if request_interval > long_sleep_time:
            logger.debug("Initiate total request count to 0")
            self.total_request_count = 0

        elif self.total_request_count >= constants.LONG_BREAK_COUNT:
            logger.debug(f"Exceed total request count, sleep {long_sleep_time}s")
            time.sleep(long_sleep_time)
            self.total_request_count = 0

        elif request_interval < sleep_time:
            remain_s = sleep_time - request_interval
            logger.debug(f"Sleep {remain_s}s for the next request")
            time.sleep(remain_s)

        return self.post_lock(*args, **kwargs)

    def post_lock(self, func, *args, **kwargs):
        """Request contents and add the total request count"""

        self.last_request_time = int(time.time())
        self.total_request_count += 1
        ritems = None
        try:
            ritems = func(*args, **kwargs)
        except Exception as err:
            logger.error(err)

        return ritems

    @property
    def sleep_time(self):
        return random.choice(
            range(
                constants.MIN_NEXT_REQUEST_INTERVAL, constants.MAX_NEXT_REQUEST_INTERVAL
            )
        )

    @property
    def long_sleep_time(self):
        return random.choice(
            range(constants.MIN_LONG_BREAK_INTERVAL, constants.MAX_LONG_BREAK_INTERVAL)
        )


def main():
    locker = Locker()

    def test_func():
        raise
        return "Done"

    with locker as fp:
        ritem = fp.lock_sleep(test_func)
        print(ritem)


if __name__ == "__main__":
    format = "%(asctime)s %(thread)d %(name)s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)
    main()
