import fastapi


class NotEnoughRightsException(fastapi.exceptions.HTTPException):
    def __init__(self) -> None:
        status_code = fastapi.status.HTTP_403_FORBIDDEN
        detail = 'Not enough rights!'
        super().__init__(status_code, detail)


class SomethingWentWrongException(fastapi.exceptions.HTTPException):
    def __init__(self, exc: str = None) -> None:
        status_code = fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = f'Something went wrong. {exc}'
        super().__init__(status_code, detail)


class UserDoesNotExistException(fastapi.exceptions.HTTPException):
    def __init__(self) -> None:
        status_code = fastapi.status.HTTP_404_NOT_FOUND
        detail = 'User does\'t exist!'
        super().__init__(status_code, detail)
