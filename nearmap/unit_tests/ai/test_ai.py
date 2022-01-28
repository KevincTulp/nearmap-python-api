from nearmap import NEARMAP
from nearmap.auth import get_api_key

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())

####################
# get tile Inputs
#################

polygon = [-87.73101994900836, 41.79082699478777, -87.73056822386012, 41.79083207215124, -87.73055971145155,
           41.79050035022655, -87.73101767903275, 41.79047834820146, -87.73101767903275, 41.79047834820146,
           -87.73101994900836, 41.79082699478777]
since = None
until = None
packs = None


def test_aiFeatures():
    ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs)
    assert len(ai_features["features"]) > 0, "Error: empty json object returned.. No Features Detected"


def test_aiClasses():
    assert len(nearmap.aiClassesV4("json")["classes"]) > 0, "Error: empty json object returned"
    assert nearmap.aiClassesV4("pandas").empty is False, "Error: empty pandas dataframe object returned"
    assert nearmap.aiClassesV4("text") is not None, "Error: empty text object returned"


def test_aiPacks():
    assert len(nearmap.aiPacksV4("json")["packs"]) > 0, "Error: empty json object returned"
    assert nearmap.aiPacksV4("pandas").empty is False, "Error: empty pandas dataframe object returned"
    assert nearmap.aiPacksV4("text") is not None, "Error: empty text object returned"

# TODO: Implement test for all other output formats
