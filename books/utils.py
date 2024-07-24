import aiofiles
from config import STATIC_PATH
import os
import uuid


async def save_image(image):
    filename = str(uuid.uuid4())
    path = STATIC_PATH / 'images' / (filename + '.webp')
    while os.path.exists(path):
        filename = str(uuid.uuid4())
        path = STATIC_PATH / 'images' / (filename + '.webp')

    async with aiofiles.open(path, 'wb') as out:
        while content := await image.read(1024):
            await out.write(content)
    return filename


async def delete_image(filename):
    path = STATIC_PATH / 'images' / (filename + '.webp')
    if os.path.exists(path):
        os.remove(path)
