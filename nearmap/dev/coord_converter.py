from math import degrees, radians, atan, sinh, tan, pi, log, cos


def latlon_to_xy(lat, lon, z):
    def sec(x):
        return 1 / cos(x)
    tile_count = pow(2, z)
    xtile = (lon + 180) / 360
    ytile = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return int(tile_count*xtile), int(tile_count*ytile)


def xy_to_latlon(xtile, ytile, z):
    n = pow(2, z)
    lon_deg = (xtile / n * 360.0) - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg


lat = 34.288171
lon = -86.281483
z = 16
e = latlon_to_xy(lat, lon, z)
print(e)
