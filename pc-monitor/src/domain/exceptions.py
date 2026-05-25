class AppError(Exception):
    status_code = 400
    error_code = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


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