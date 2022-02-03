

def dms_to_dd(d, m, s):
    dd = d + float(m)/60 + float(s)/3600
    return dd


def gen_coord(d, m, s):
    return d + dms_to_dd(d, m, s)


def process_coords(dms_coord):
    d, m, sd = dms_coord.split('-')
    s, dir = (sd[:-1], sd[-1])
    return gen_coord(int(d), int(m), float(s)) * (-1 if dir in ['W', 'S'] else 1)


def convert_coords_dms_to_dd(in_dms_coords):
    results = []
    for i in in_dms_coords:
        _lat, _lon = i
        lat = process_coords(_lat)
        lon = process_coords(_lon)
        results.append([lat, lon])
    return results


if __name__ == "__main__":

    in_dms_coords = [
        ["34-28-40.9000N", "093-05-46.4000W"],
        ["34-43-45.9862N", "092-13-29.1968W"],
        ["33-27-13.4000N", "093-59-27.7000W"],
        ["14-12-58.0040S", "169-25-24.7780W"],
        ["14-11-03.6350S", "169-40-12.3600W"],
        ["14-19-53.9840S", "170-42-41.4110W"],
        ["35-09-16.6120N", "114-33-33.5960W"]]

    results = convert_coords_dms_to_dd(in_dms_coords)

    print(results)
