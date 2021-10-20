from nearmap import NEARMAP
from nearmap.auth import get_api_key
try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps

# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
nearmap = NEARMAP(get_api_key())
print(f"My API Key Is: {nearmap.api_key}")

###################
# User Parameters
#################

polygon = [-87.73101994900836, 41.79082699478777,
           -87.73056822386012, 41.79083207215124,
           -87.73055971145155, 41.79050035022655,
           -87.73101767903275, 41.79047834820146,
           -87.73101767903275, 41.79047834820146,
           -87.73101994900836, 41.79082699478777]
since = None  # Since Data ex: "2018-08-01"
until = None  # Until Date ex: "2021-07-09"
limit = 50
offset = None
fields = None
sort = None
overlap = None
include = None
exclude = None
lat_lon_direction = "yx"

##########
# Script
########

polygon_coverage = nearmap.polyV2(polygon, since, until, limit, offset, fields, sort, overlap, include, exclude,
                                  lat_lon_direction)
print(dumps(polygon_coverage, indent=4, sort_keys=True))

surveys = polygon_coverage.get("surveys")
assert len(surveys) > 0, "Error: empty json object returned.. No Features Detected"

num_surveys = len(surveys)
print(f"Total Surveys: {num_surveys}\n")

locations = [surveys[i].get('location') for i in list(range(0, num_surveys))]
locations_formatted = [[i.get('region'), i.get('state'), i.get('country')] for i in locations]
print(f"Capture Location: {locations_formatted}\n")

capture_dates = [surveys[i].get('captureDate') for i in list(range(0, num_surveys))]
print(f"Image Capture Dates: {capture_dates}\n")

first_last_photo_capture_time = [[surveys[i].get('firstPhotoTime'), surveys[i].get('lastPhotoTime')]
                                 for i in list(range(0, num_surveys))]
print(f"First & Last Photo Capture Time: {first_last_photo_capture_time}\n")

timezone = [surveys[i].get('timezone') for i in list(range(0, num_surveys))]
print(f"Capture Timezone: {timezone}\n")

utc_offset = [surveys[i].get('utcOffset') for i in list(range(0, num_surveys))]
print(f"Capture Timezone: {utc_offset}\n")

pixel_sizes = [surveys[i].get('pixelSize') for i in list(range(0, num_surveys))]
print(f"Max Pixel Size: {pixel_sizes}\n")

vert_zoom_levels = [item for sublist in [[v.get('scale') for v in surveys[i].get('resources').get('tiles') if
                                          v.get('type') == 'Vert'] for i in list(range(0, num_surveys))]
                    for item in sublist]
print(f"Vert Ortho Max Zoom Levels: {vert_zoom_levels}\n")

tags = [surveys[i].get('tags') for i in list(range(0, num_surveys))]
print(f"Tags: {tags}\n")


def panorama_max_zoom_levels(in_surveys):
    panorama_list = list()
    for survey in in_surveys:
        try:
            zoom = [v.get('scale') for v in survey.get('resources').get('tiles') if v.get('type') == 'North']
            if zoom:
                panorama_list.extend(zoom)
            else:
                panorama_list.append(None)
        except TypeError:
            panorama_list.append(None)
    return panorama_list


print(f"Panorama Max Zoom Levels: {panorama_max_zoom_levels(surveys)} \n")


def ai_captures(in_surveys):
    ai_list = list()
    for survey in in_surveys:
        try:
            ai_list.append(len(survey.get('resources').get('aifeatures')[0].get('properties').get('classes')))
        except TypeError:
            ai_list.append(None)
    return ai_list


print(f"AI Capture Count: {ai_captures(surveys)}\n")


def ai_classes(in_surveys):
    ai_list = list()
    for survey in in_surveys:
        try:
            ai_list.append([i.get('description') for i in
                            survey.get('resources').get('aifeatures')[0].get('properties').get('classes')])
        except TypeError:
            ai_list.append(None)
    return ai_list


print("AI Classes:")
[print(i) for i in ai_classes(surveys)]
