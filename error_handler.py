class ErrorHandler(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class BadCRC(ErrorHandler):
    def __init__(self, message="Bad CRC", error_code=None):
        super().__init__(message, error_code)


class AFTBadAmount(ErrorHandler):
    def __init__(self, message="AFT Bad Amount", error_code=None):
        super().__init__(message, error_code)


class BadTransactionID(ErrorHandler):
    def __init__(self, message="Bad Transaction ID", error_code=None):
        super().__init__(message, error_code)


class NoSasConnection(ErrorHandler):
    def __init__(self, message="No SAS Connection", error_code=None):
        super().__init__(message, error_code)


class SASOpenError(ErrorHandler):
    def __init__(self, message="SAS Open Error", error_code=None):
        super().__init__(message, error_code)


class EMGGpollBadResponse(ErrorHandler):
    def __init__(self, message="EMGGPoll bad response", error_code=None):
        super().__init__(message, error_code)
