#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
Instagram content parser by each step

* Scraping top hot medias in tags, including like counts, image url, etc
* Scraping comments and location id of each top hot media
* Scraping location information of each media, e.g., latitude, longitude, address
"""

import abc
import json
import logging
import os
from datetime import datetime
from itertools import chain
from pathlib import Path

from igramscraper.instagram import Instagram
from sqlalchemy import desc, select
from sqlalchemy.inspection import inspect

from models import LocationSchema, Media, MediaSchema
from utils import connector, constants

logger = logging.getLogger(__name__)


class Extractor(Instagram, metaclass=abc.ABCMeta):
    def __init__(self):
        super().__init__()

    @abc.abstractclassmethod
    def parse_data(self):
        return NotImplemented

    @abc.abstractclassmethod
    def save_to_db(self, data, schema, ref_table=None, ref_col=None, **kwargs):
        """
        Connect to database and save medias information

        :param Union[object, list] data: Data that needs to update into database
        :param object schema: A marshmallow schema
        :param object ref_table: SQLAlchemy table class
        :param string ref_col: A column name that needs to be checked
        :param **kwargs: Additional content that needs to update into database
        """
        data = self.drop_none_attr(data)

        with connector.ConnectFromPool() as session:
            load_data = schema.load(data, session=session)

            # Update additional content with same table
            if kwargs != {} and ref_table is None:
                for attr, v in kwargs.items():
                    self.update_media_attr(load_data, attr, v)

            if isinstance(load_data, list):
                for load_data_ in load_data:
                    session.merge(load_data_)
            else:
                session.merge(load_data)

            # Update additional content with different table
            if (ref_table is not None) and (ref_col is not None):
                self._update_ref_table(session, load_data, ref_table, ref_col, **kwargs)

    @staticmethod
    def _update_ref_table(session, load_data, ref_table, ref_col, **kwargs):
        """Update *checked_time column in reference table"""

        assert not isinstance(
            load_data, list
        ), "Reference data must be an object not list"
        assert kwargs != {}, "No additional content to be added"

        # Get name of primary key
        table_class = session.identity_key(instance=load_data)[0]
        pk_name = inspect(table_class).primary_key[0].name

        results = (
            session.query(ref_table)
            .filter(getattr(ref_table, ref_col) == getattr(load_data, pk_name))
            .with_for_update()
            .all()
        )

        for attr, v in kwargs.items():
            Extractor.update_media_attr(results, attr, v)

    @staticmethod
    def update_media_attr(obj, attr_name, value):
        """According to obj type, object of list or single object to update media attributes"""

        if isinstance(obj, list):
            for obj_ in obj:
                setattr(obj_, attr_name, value)

        else:
            setattr(obj, attr_name, value)

        return obj

    @staticmethod
    def drop_none_attr(obj):
        """Filter out None attributes, avoid to overwrite existed records in database"""

        if isinstance(obj, list):
            obj_list = []
            for obj_ in obj:
                obj_list.append({k: v for k, v in obj_.items() if v is not None})

            return obj_list

        elif isinstance(obj, dict):
            obj = {k: v for k, v in obj.items() if v is not None}

            return obj

    def get_source_list(self, check_time_column, check_column):
        """
        Check for information in database

        :param string check_time_column: Column name in table about checking time
        :param string check_column: Column name in table about checking column
        :return: Unchecked map object
        :rtype map
        """
        with connector.ConnectFromPool() as session:
            results = session.execute(
                select(Media)
                .where(getattr(Media, check_time_column) == None)
                .where(getattr(Media, check_column) != None)
                .order_by(desc(Media.likes_count))
            )

        results = results.all()
        if results == []:
            logger.info(f"No {self} needs to be checked")
            return
        else:
            results = list(chain.from_iterable(results))  # Flatten one level of nesting
            logger.info(f"{len(results)} {self}(s) need to be checked")

            src_list = map(lambda x: getattr(x, check_column), results)
            return src_list

    # @abc.abstractclassmethod
    # def output(self):
    #     return NotImplemented


class TopMediasExtractor(Extractor):
    def __init__(self):
        self.schema = MediaSchema(many=True)
        self.tag = None
        super().__init__()

    def __repr__(self):
        return "top_medias"

    def parse_data(self, tag):
        """
        Query each food-related tag and filter out non food-related media

        :param string tag: Food related tag for scraping content from Instagram
        """
        self.tag = tag
        medias = self.get_current_top_medias_by_tag_name(tag)
        food_medias = self.filter_food_media(medias)

        return food_medias

    @staticmethod
    def filter_food_media(medias):
        """
        Filter media that only contains food-related images

        :param list medias: The top medias in the instagram tag
        :return: Food-related medias
        :rtype list
        """

        food_medias = []
        for media in medias:
            accessibility_caption = media.accessibility_caption
            if accessibility_caption is None:
                continue

            srch_food = constants.get_img_food_range_regex()
            if srch_food.search(accessibility_caption):
                food_medias.append(media)

        return food_medias

    def get_source_list(self):
        return constants.SEARCH_TAGS

    def save_to_db(self, data):
        content = {"tag": self.tag}
        super().save_to_db(data, self.schema, **content)

    # def output(self, tag, data, target_path="./data/top_tags"):
    #     target_path = Path(os.path.join(target_path, tag))
    #     target_path.mkdir(parents=True, exist_ok=True)
    #     fp = target_path.joinpath(self.date + ".json")

    #     with open(fp, "w", encoding="utf-8") as f:
    #         json.dump(data, f)


class MediaExtractor(Extractor):
    def __init__(self):
        self.schema = MediaSchema(many=False)
        self.check_time_column = "media_checked_time"
        self.check_column = "short_code"
        super().__init__()

    def __repr__(self):
        return "media"

    def get_source_list(self):
        return super().get_source_list(self.check_time_column, self.check_column)

    def parse_data(self, short_code):
        return self.get_medias_by_code(short_code)

    @staticmethod
    def get_comments_jsonfmt(data):
        comments = data.get("comments", [])

        if comments == []:
            return data

        else:
            comments_dict = {}
            for comment in comments:
                owner_id = comment.owner.identifier
                text = comments_dict.get(owner_id, [])

                text.append(comment.text)
                comments_dict.update({owner_id: text})

            data.update({"comments": comments_dict})
            return data

    def save_to_db(self, data):
        data = self.get_comments_jsonfmt(data)
        dt = int(datetime.now().timestamp())
        content = {self.check_time_column: dt}

        super().save_to_db(data, self.schema, **content)


class LocationExtractor(Extractor):
    def __init__(self):
        self.schema = LocationSchema(many=False)
        self.check_time_column = "location_checked_time"
        self.check_column = "location_id"
        super().__init__()

    def __repr__(self):
        return "location"

    def get_source_list(self):
        src_list = super().get_source_list(self.check_time_column, self.check_column)

        # Deduplicates location_id
        return list(dict.fromkeys(src_list))

    def parse_data(self, loc_id):
        return self.get_location_by_id(loc_id)

    @staticmethod
    def get_address_jsonfmt(data):
        address = data.get("address_json", None)

        if address is not None:
            address_dict = json.loads(address)
            data.update({"address_json": address_dict})

        return data

    def save_to_db(self, data):
        data = self.get_address_jsonfmt(data)
        dt = int(datetime.now().timestamp())
        content = {self.check_time_column: dt}

        super().save_to_db(
            data, self.schema, ref_table=Media, ref_col=self.check_column, **content
        )


class CommentsExtractor(Extractor):
    pass


def main():
    tag = ["新竹美食"]
    extractor = MediaExtractor()
    res = extractor.get_source_list()
    if res is not None:
        print(list(res))

    # top_medias = extractor.parse_data(tag[0])
    # schema = extractor.schema

    # data = schema.dump(top_medias)
    # extractor.output(tag[0], data)


if __name__ == "__main__":
    format = "%(asctime)s %(thread)d %(name)s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)
    main()
