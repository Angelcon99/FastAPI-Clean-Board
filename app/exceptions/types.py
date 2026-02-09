from typing import Any, Optional

from pydantic import EmailStr


class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        details: Any = None,
        status_code: int = 500,
        headers: Optional[dict[str, str]] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        self.headers = headers
        super().__init__(self.message)

# ---------------------- Post ----------------------
class PostNotFoundException(BaseAppException):
    def __init__(
        self,
        post_id: int,
        message: str | None = None
    ):
        if message is None:
            message = f"Post with ID {post_id} not found."
        super().__init__(
            message, 
            code="POST_NOT_FOUND", 
            details={"post_id": post_id},
            status_code=404
        )

# ---------------------- User ----------------------
class UserNotFoundException(BaseAppException):
    def __init__(
        self,
        user_id: int,
        message: str = "User not found."
    ):
        super().__init__(
            message = message,
            code="USER_NOT_FOUND",
            details={"user_id":user_id},
            status_code=404
        )

class UserMismatchException(BaseAppException):
    def __init__(
        self,
        message: str = "User Mismatch",
    ):
        super().__init__(
            message = message,
            code="USER_MISMATCH",
            status_code=403
        )

class UserExistEmailException(BaseAppException):
    def __init__(
        self,
        email: EmailStr,
        message: str | None = None
    ):
        if message is None:
            message = f"Email '{email}' is already taken."
        super().__init__(
            message=message,
            code="EMAIL_EXISTS",
            details={"email": email},
            status_code=409
        )
                
class UserExistNicknameException(BaseAppException):
    def __init__(
        self, 
        nickname: str,
        message: str | None = None
    ):
        if message is None:
            message = f"Nickname '{nickname}' is already taken."
        super().__init__(
            message=message,
            code="NICKNAME_EXISTS",
            details={"nickname": nickname},
            status_code=409
        )
        
class PasswordValidationException(BaseAppException):
    def __init__(
        self, 
        message: str
    ):
        super().__init__(
            message=message, 
            code="PASSWORD_VALIDATION_FAILED",
            status_code=400
        )

# ---------------------- Comment ----------------------
class CommentNotFoundException(BaseAppException):
    def __init__(
        self, 
        comment_id: int, 
        message: str | None = None
    ):
        if message is None:
            message = f"Comment with ID {comment_id} not found."
        super().__init__(
            message, code="COMMENT_NOT_FOUND", 
            details={"comment_id": comment_id},
            status_code=404
        )        

class ReplyDepthLimitExceededException(BaseAppException):
    def __init__(
        self,
        parent_id: int,
        message: str = "Replies to replies are not allowed."
    ):
        super().__init__(
            message=message,
            code="REPLY_DEPTH_LIMIT_EXCEEDED",
            details={"parent_id": parent_id},
            status_code=400
        )
        
class CommentPostMismatchException(BaseAppException):
    def __init__(
        self, 
        parent_id: int,
        parent_post_id: int, 
        request_post_id: int,
        message: str = "The parent comment does not belong to this post."
    ):
        super().__init__(
            message=message,
            code="COMMENT_POST_MISMATCH",
            details={
                "parent_id": parent_id,
                "parent_post_id": parent_post_id,
                "request_post_id": request_post_id
            },
            status_code=400
        )
        
# ---------------------- Auth ----------------------
class UnauthorizedActionException(BaseAppException):
    def __init__(
        self, 
        message: str = "You are not authorized to perform this action."
    ):
        super().__init__(
            message, 
            code="UNAUTHORIZED_ACTION",
            status_code=403
        )

class InvalidTokenException(BaseAppException):
    def __init__(
        self,
        message: str = "Invalid authentication token.",
    ):
        super().__init__(
            message = message,
            code="INVALID_TOKEN",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenPayloadInvalidException(BaseAppException):
    def __init__(
        self,
        message: str = "Invalid token payload."
    ):
        super().__init__(
            message=message,
            code="TOKEN_PAYLOAD_INVALID",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )
        
class RefreshTokenExpiredException(BaseAppException):
    def __init__(
        self,
        message: str = "Refresh token has expired."
    ):
        super().__init__(
            message = message,
            code="REFRESH_TOKEN_EXPIRED",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )

class RefreshTokenNotFoundException(BaseAppException):
    def __init__(
        self,
        message: str = "Refresh token not found."
    ):
        super().__init__(
            message=message,
            code="REFRESH_TOKEN_NOT_FOUND",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )
        
class InvalidCredentialsException(BaseAppException):
    def __init__(
        self,
        message: str = "Invalid email or password."
    ):
        super().__init__(
            message = message,
            code="INVALID_CREDENTIALS",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )

# ---------------------- Rule ----------------------
class RuleViolationException(BaseAppException):
    def __init__(
        self,
        message: str = "Admin privileges are required to access this resource", 
        rule_code: str | None = None,
        details: Any = None
    ):
        merged_details = {"rule_code": rule_code}
        if details:
            merged_details.update(details)

        super().__init__(
            message=message,
            code="RULE_VIOLATION",
            details=merged_details,
            status_code=403
        )
        
# ---------------------- Common ----------------------
class InternalServerException(BaseAppException):
    def __init__(
        self,        
        message: str = "An unexpected error occurred. Please try again later.",
        details: dict | str | None = None,
    ):
        super().__init__(
            message=message,
            code="INTERNAL_SERVER_ERROR",
            details=details,
            status_code=500,
        )