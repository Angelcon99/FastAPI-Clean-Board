from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"

    def __str__(self) -> str:        
        return self.value

class PostCategory(str, Enum):    
    GENERAL = "general"
    INFORMATION = "information"
    EVENT = "event"

    def __str__(self) -> str:        
        return self.value