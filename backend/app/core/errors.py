class AppError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "行程生成服务暂时不可用，请稍后再试。") -> None:
        super().__init__(message=message, status_code=503)


class UpstreamServiceError(AppError):
    def __init__(self, message: str = "行程生成服务暂时不可用，请稍后再试。") -> None:
        super().__init__(message=message, status_code=502)


class LLMOutputError(Exception):
    pass
