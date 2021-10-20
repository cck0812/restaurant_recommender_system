import logging

from ig_extractor import (
    CommentsExtractor,
    LocationExtractor,
    MediaExtractor,
    TopMediasExtractor,
)
from locker import Locker
from models import LocationSchema

logger = logging.getLogger(__name__)


def execute(src_list=None, extractor=None):

    for src in src_list:
        with Locker() as lock:
            data = lock.lock_sleep(extractor.parse_data, src)

        if data is None:
            logger.error(f"Got no data from {extractor!r} with {src!r}")
        else:
            schema = extractor.schema
            dump_data = schema.dump(data)
            extractor.save_to_db(dump_data)
            logger.info(f"Executed job of {extractor!r} with {src!r} sucessfully !")


def main():
    extractor_cls = LocationExtractor
    extractor = extractor_cls()
    # extractor.with_credentials("<id>", "<password>")
    # extractor.login()

    src_list = extractor.get_source_list()

    if src_list is not None:
        execute(src_list, extractor)


if __name__ == "__main__":
    format = "%(asctime)s %(thread)d %(name)s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)
    main()
