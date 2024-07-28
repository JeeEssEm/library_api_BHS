from models import Rights


async def is_admin(user):
    return user.rights == Rights.admin


async def is_librarian(user):
    return (user.rights == Rights.librarian or user.rights == Rights.admin)
