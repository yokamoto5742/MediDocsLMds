class AppError(Exception):
    pass

class APIError(AppError):
    pass

class DatabaseError(AppError):
    pass
