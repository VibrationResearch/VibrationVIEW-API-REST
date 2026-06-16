class APIError(Exception):
    """Raised by route helpers to return a specific HTTP error through @handle_errors."""

    def __init__(self, message, error_code="GENERIC_ERROR", http_status=400):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
