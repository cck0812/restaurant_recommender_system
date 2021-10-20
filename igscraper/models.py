#!/usr/bin/env python
# -*-coding:utf-8 -*-

import sqlalchemy as sa
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base

from utils.connector import ConnectFromPool

Base = declarative_base()
engine = ConnectFromPool().engine


# Declare models
class Media(Base):
    __tablename__ = "top_medias"
    short_code = sa.Column(sa.String, primary_key=True)
    created_time = sa.Column(sa.Integer)
    media_checked_time = sa.Column(sa.Integer)
    location_checked_time = sa.Column(sa.Integer)
    caption = sa.Column(sa.String)
    likes_count = sa.Column(sa.Integer)
    comments_count = sa.Column(sa.Integer)
    comments = sa.Column(JSON)
    image_high_resolution_url = sa.Column(sa.String)
    accessibility_caption = sa.Column(sa.String)
    location_id = sa.Column(sa.String)
    tag = sa.Column(sa.String)


class Location(Base):
    __tablename__ = "location"
    identifier = sa.Column(sa.String, primary_key=True)
    name = sa.Column(sa.String)
    lat = sa.Column(sa.String)
    lng = sa.Column(sa.String)
    address_json = sa.Column(JSON)


class Comment(Base):
    __tablename__ = "comment"
    identifier = sa.Column(sa.String, primary_key=True)
    owner = sa.Column(sa.String)
    text = sa.Column(sa.String)


Base.metadata.create_all(engine)


# Generate marshmallow schemas
class MediaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Media
        include_relationships = True
        load_instance = True
        unknown = EXCLUDE


class LocationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        include_relationships = True
        load_instance = True
        unknown = EXCLUDE


class CommentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Comment
        include_relationships = True
        load_instance = True
        unknown = EXCLUDE
