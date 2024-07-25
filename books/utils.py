import aiofiles
from config import STATIC_PATH
import os
import uuid
from . import schemes
from aiocsv import AsyncReader
from fastapi import UploadFile
from typing import List, Union
from sqlalchemy.orm import Session
from models import Book


async def generate_filename(path, ext):
    filename = str(uuid.uuid4()) + ext
    while os.path.exists(path / filename):
        filename = str(uuid.uuid4()) + ext
    return filename


async def save_image(image: UploadFile):
    path = STATIC_PATH / 'images'
    filename = await generate_filename(path, '.webp')
    path = path / filename
    await save_file(image, path)
    return filename


async def save_file(file, path):
    async with aiofiles.open(path, 'wb') as out:
        while content := await file.read(1024):
            await out.write(content)


async def delete_image(filename):
    path = STATIC_PATH / 'images' / filename
    if os.path.exists(path):
        os.remove(path)


def converter_book_scheme(book):
    return schemes.ShortBookForm(
        id=book.id,
        title=book.title,
        authors=book.authors,
        edition_date=book.edition_date
    )


async def remove_book_image(filename):
    path = STATIC_PATH / 'images' / filename
    if os.path.exists(path):
        os.remove(path)


async def handle_books_csv(file: UploadFile, db: Session, images: List[Union[UploadFile, None]]):
    path = STATIC_PATH / 'temp'
    filename = await generate_filename(path, '.csv')
    path = path / filename
    await save_file(file, path)
    try:
        async with aiofiles.open(path, mode='r', encoding='utf_8_sig') as f:
            reader = AsyncReader(f, delimiter=';', quotechar='"')
            await reader.__anext__()

            async for line in reader:
                title, authors, desc, amount, edition, image_filename = line
                book = Book(
                    title=title,
                    authors=authors,
                    description=desc,
                    amount=amount,
                    edition_date=edition,
                    is_private=False
                )
                if image_filename:
                    image = list(filter(lambda item: item.filename == image_filename, images))
                    if image:
                        filename = await save_image(image[0])
                        book.image = filename
                db.add(book)
                db.commit()
    finally:
        os.remove(path)
