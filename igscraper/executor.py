import argparse
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


def scrap_ig_content(src_list=None, extractor=None):

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


def execute(extractor):
    src_list = extractor.get_source_list()

    if src_list is not None:
        scrap_ig_content(src_list, extractor)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "ig_parser",
        nargs="?",
        help="Valid option: top_medias | media_check | location_check",
    )
    args = arg_parser.parse_args()

    if args.ig_parser == "top_medias":
        extractor = TopMediasExtractor()

    elif args.ig_parser == "media_check":
        extractor = MediaExtractor()

    elif args.ig_parser == "location_check":
        extractor = LocationExtractor()

    elif args.ig_parser:
        raise ValueError("Please assign valid ig_parser argument !")

    else:
        # Manual Debug Process
        extractor = LocationExtractor()
        # extractor.with_credentials("<id>", "<password>")
        # extractor.login()

    execute(extractor=extractor)


if __name__ == "__main__":
    format = "%(asctime)s %(thread)d %(name)s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)
    main()
