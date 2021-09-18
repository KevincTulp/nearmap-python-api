from nearmap import NEARMAP
from nearmap.auth import get_api_key

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())

print(nearmap)
####################
# get tile Inputs
#################

polygon = [-87.73101994900836,41.79082699478777,-87.73056822386012,41.79083207215124,-87.73055971145155,41.79050035022655,-87.73101767903275,41.79047834820146,-87.73101767903275,41.79047834820146,-87.73101994900836,41.79082699478777]
point = [-87.73101994900836, 41.79082699478777]
x = 16
y = 57999
z = 39561


def test_polyV2():
    assert len(nearmap.polyV2(polygon)["surveys"]) > 0, "Error: empty json object returned... No Features Detected"


def test_pointV2():
    assert len(nearmap.pointV2(point)["surveys"]) > 0, "Error: empty json object returned... No Features Detected"


def test_surveyV2():
    assert len(nearmap.surveyV2(polygon)["features"]) > 0, "Error: empty json object returned.. No Features Detected"


def test_coverageV2():
    assert len(nearmap.coverageV2()["features"]) > 0, "Error: empty json object returned.. No Features Detected"


