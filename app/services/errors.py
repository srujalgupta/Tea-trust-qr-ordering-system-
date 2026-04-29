class AppError(Exception):
    status_code = 400
    error_code = "bad_request"

    def __init__(self, message, status_code=None, error_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class ValidationError(AppError):
    status_code = 400
    error_code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class PaymentError(AppError):
    status_code = 400
    error_code = "payment_error"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "forbidden"
