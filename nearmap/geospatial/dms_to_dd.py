

def dms_to_dd(d, m, s):
    return d + float(m)/60 + float(s)/3600


def process_coord(dms_coord, delimeter="-"):
    d, m, sd = dms_coord.split(delimeter)
    s, dir = (sd[:-1], sd[-1])
    return dms_to_dd(int(d), int(m), float(s)) * (-1 if dir in ['W', 'S'] else 1)


def convert_coords_dms_to_dd(in_dms_coords, delimeter="-"):
    return [process_coord(in_dms_coords[0], delimeter), process_coord(in_dms_coords[1], delimeter)]


def convert_coord_list_dms_to_dd(in_dms_coords, delimeter="-"):
    return [convert_coords_dms_to_dd(i, delimeter) for i in in_dms_coords]


if __name__ == "__main__":

    #################################
    # Convert DMS coord list to DD Coord list
    ###############################
    in_dms_coords = [
        ["34-28-40.9000N", "093-05-46.4000W"],
        ["34-43-45.9862N", "092-13-29.1968W"],
        ["33-27-13.4000N", "093-59-27.7000W"],
        ["14-12-58.0040S", "169-25-24.7780W"],
        ["14-11-03.6350S", "169-40-12.3600W"],
        ["14-19-53.9840S", "170-42-41.4110W"],
        ["35-09-16.6120N", "114-33-33.5960W"]]

    delimeter = "-"
    results = convert_coord_list_dms_to_dd(in_dms_coords, delimeter)
    print(f"processed coordinates as: {results}")

    #################################
    # Convert DMS coord to DD Coord
    ###############################
    in_dms_coord = ["34-28-40.9000N", "093-05-46.4000W"]
    delimeter = "-"
    result = convert_coords_dms_to_dd(in_dms_coord, delimeter)
    print(f"processed coord pair as: {result}")
