import os
import random
import re

DB_URL = "postgresql://airflow:airflow@postgres/airflow"
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 0

SEARCH_TAGS = ["台北美食"]
IMG_FOOD_RANGE = ["food", "drink", "dessert"]

MIN_NEXT_REQUEST_INTERVAL = 30
MAX_NEXT_REQUEST_INTERVAL = 60
MIN_LONG_BREAK_INTERVAL = 300
MAX_LONG_BREAK_INTERVAL = 600
LONG_BREAK_COUNT = 10


def get_search_tags():
    if isinstance(SEARCH_TAGS, str):
        return SEARCH_TAGS.split()

    return SEARCH_TAGS


def get_img_food_range_regex():
    global IMG_FOOD_RANGE

    if isinstance(IMG_FOOD_RANGE, str):
        IMG_FOOD_RANGE = IMG_FOOD_RANGE.split()

    return re.compile("(?:May be).*?({})".format("|".join(IMG_FOOD_RANGE)))


def get_next_request_interval():
    return random.choice(range(MIN_NEXT_REQUEST_INTERVAL, MAX_NEXT_REQUEST_INTERVAL))[0]


def get_db_param_dict():
    prefix = "DB_"
    db_param_dict = {
        k.strip(prefix).lower(): v for k, v in globals().items() if k.startswith(prefix)
    }
    return db_param_dict


def setup_constants():
    GLOBAL_VARS = globals()

    for key, val in GLOBAL_VARS.items():
        env_var = os.environ.get(key)
        if env_var is not None:
            GLOBAL_VARS.update({key: env_var})


setup_constants()
