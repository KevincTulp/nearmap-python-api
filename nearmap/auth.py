####################################
#   File name: auth.py
#   About: simple authentication using credentials in auxillary api_key.json file
#   Author: Geoff Taylor | Sr Solution Architect | Nearmap
#   Date created: 7/7/2021
#   Python Version: 3.8
####################################

try:
    from ujson import loads
except ModuleNotFoundError:
    from json import loads

from os.path import realpath, dirname, join


def get_api_key():
    # load source credentials
    api_key = join(dirname(realpath(__file__)), "api_key.json")
    f = open(api_key, "r")
    my_json = loads(f.read())
    # Closing file
    f.close()
    return my_json['API_KEY']
