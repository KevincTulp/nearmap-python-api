# Requirement: OWSLib https://geopython.github.io/OWSLib/

from owslib.wms import WebMapService
from nearmap.auth import get_api_key

wms = WebMapService(f"https://api.nearmap.com/wms/v1/latest/apikey/{get_api_key()}?request=GetCapabilities",
                    version='1.1.1')

print(f"Type: {wms.identification.type}")
print(f"Version: {wms.identification.version}")
print(f"Title: {wms.identification.title}")
print(f"Abstract: {wms.identification.abstract}")
print(f"Provider Name: {wms.provider.name}")
print(f"Provider Address: {wms.provider.contact.address}")
contents = list(wms.contents)
print("Contents:")
[print(f"\t - {p} | \n\t\t Title: {wms[p].title} \n\t\t Queryable: {wms[p].queryable} \n\t\t Opaque: {wms[p].opaque} \n\t\t boundingBox: {wms[p].boundingBox} \n\t\t boundingBoxWGS84: {wms[p].boundingBoxWGS84} \n\t\t crsOptions: {wms[p].crsOptions} \n\t\t styles: {wms[p].styles}") for p in contents]

print("\n Available Methods, URL's, and Formats")
[print(f"\t Operations: - {op.name} | Methods: {wms.getOperationByName(op.name).methods} | Format Options: {wms.getOperationByName(op.name).formatOptions}") for op in wms.operations]


def size_formatter(extent, max_dimension):
    length = abs(extent[2] - extent[0])
    width = abs(extent[3] - extent[1])
    size = (max_dimension, max_dimension)
    if length > width:
        size = (max_dimension, int((width/length)*max_dimension))
    elif length < width:
        size = (int((length/width)*max_dimension), max_dimension)
    return size


extent = (-86.7824419839999, 33.4825045740001, -86.752034668, 33.5119028180001)
max_dimension = 6000  # Maximum 6k pixels

img = wms.getmap(layers=['global_mosaic'],
                 styles=['visual_bright'],
                 srs='EPSG:4326',
                 bbox=extent,
                 size=size_formatter(extent, max_dimension),
                 format='image/jpeg',
                 transparent=True
                 )
out = open('test_ortho.jpg', 'wb')
out.write(img.read())
out.close()
