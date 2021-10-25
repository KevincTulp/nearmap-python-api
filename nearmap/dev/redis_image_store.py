from PIL import Image
import redis
from io import BytesIO
from pathlib import Path


def to_redis(redis_server, in_tile):
    image_name = Path(in_tile).stem
    output = BytesIO()
    im = Image.open(in_tile)
    im.save(output, format=im.format)
    redis_server.set(image_name, output.getvalue())
    output.close()
    return image_name


def from_redis(redis_server, tile_name, out_format):
    tile = redis_server.get(tile_name)
    if tile:
        if out_format.lower() == "binary":
            tile = redis_server.get(tile_name)
            return tile
        else:
            f = Image.open(tile)
            return f.save(tile_name)
    else:
        return None


if __name__ == "__main__":
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    in_tile = "id_z_x_y.jpg"
    redis_tile = to_redis(redis_server=r, in_tile=in_tile)
    image_tile = from_redis(redis_server=r, tile_name=in_tile, out_format="binary")

    #  TODO Assess Asyncio + Celery when streaming tiles
    #  https://stackoverflow.com/questions/39815771/how-to-combine-celery-with-asyncio
