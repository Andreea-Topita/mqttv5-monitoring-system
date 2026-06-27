# clasa de baza pentru toare erorile aplicatiei
# mosteneste exception, deci obiectele pot fi aruncate prin raise, try except, etc

class AppError(Exception):
    # cod http implicit asociat erorii, clasele il pot suprascrie
    status_code = 400
    
    # clasele copil suprascriu codul de eroare specific
    error_code = "APP_ERROR"

    # constructor primeste mesajul concret care explica eroarea
    def __init__(self, message: str):
        # apeleaza constructorul clasei exception si ii transmite mesajul
        self.message = message
        super().__init__(message)

# serviciul exprima direct problema si handlerul global din API transforma exceptia intr un raspuns http
class BusinessValidationError(AppError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class AlreadyConnectedError(AppError):
    status_code = 409
    error_code = "ALREADY_CONNECTED"


class NotConnectedError(AppError):
    status_code = 409
    error_code = "NOT_CONNECTED"


class SubscriptionNotFoundError(AppError):
    status_code = 404
    error_code = "SUBSCRIPTION_NOT_FOUND"


class PeriodicPublishAlreadyRunningError(AppError):
    status_code = 409
    error_code = "PERIODIC_PUBLISH_ALREADY_RUNNING"


class InvalidQoSError(AppError):
    status_code = 400
    error_code = "INVALID_QOS"


class InvalidTopicError(AppError):
    status_code = 400
    error_code = "INVALID_TOPIC"


class ConnectionFailedError(AppError):
    status_code = 400
    error_code = "CONNECTION_FAILED"


class PublishError(AppError):
    status_code = 400
    error_code = "PUBLISH_ERROR"

class PeriodicPublishNotRunningError(AppError):
    status_code = 409
    error_code = "PERIODIC_PUBLISH_NOT_RUNNING"

class UserAlreadyExistsError(AppError):
    status_code = 409
    error_code = "USER_ALREADY_EXISTS"


class InvalidCredentialsError(AppError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"