import random
import re

DB_PARAM = {
    "url": "postgresql://airflow:airflow@postgres/airflow",
    "pool_size": 5,
    "max_overflow": 0,
}

SEARCH_TAGS = ["苗栗美食"]
IMG_FOOD_RANGE = ["food", "drink", "dessert"]

MIN_NEXT_REQUEST_INTERVAL = 30
MAX_NEXT_REQUEST_INTERVAL = 60
MIN_LONG_BREAK_INTERVAL = 300
MAX_LONG_BREAK_INTERVAL = 600
LONG_BREAK_COUNT = 10


def get_img_food_range_regex():
    return re.compile("(?:May be).*?({})".format("|".join(IMG_FOOD_RANGE)))


def get_next_request_interval():
    return random.choice(range(MIN_NEXT_REQUEST_INTERVAL, MAX_NEXT_REQUEST_INTERVAL))[0]
