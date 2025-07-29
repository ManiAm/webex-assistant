
import operator
from functools import reduce


def get_value(dictionary, key_list):

    try:
        return reduce(operator.getitem, key_list, dictionary)
    except Exception:
        return None
