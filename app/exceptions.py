
##USER
class EmailAlreadyExistsException(Exception):
    pass
class UserNotFoundException(Exception):
    pass
class InvalidCredentialsException(Exception):
    pass
class UserInactiveException(Exception):
    pass
class UserNotVerifiedException(Exception):
    pass
class UserAlreadyVerifiedException(Exception):
    pass

##TOKEN
class InvalidTokenException(Exception):
    pass
class TokenExpiredException(Exception):
    pass
class InvalidAccessTokenException(Exception):
    pass

##RATE-LIMIT
class RateLimitExceededException(Exception):
    pass
##EMAIL
class EmailServiceException(Exception):
    pass

class CoreServiceException(Exception):
    pass

##OTHER
class UnexpectedException(Exception):
    pass

