from enum import Enum


class MethodologyType(str, Enum):
    ISHIKAWA = "ishikawa"
    EIGHT_D = "8d"
    FIVE_WHY = "5why"
    PDCA = "pdca"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IshikawaCategory(str, Enum):
    MAN = "man"
    MACHINE = "machine"
    METHOD = "method"
    MATERIAL = "material"
    MEASUREMENT = "measurement"
    ENVIRONMENT = "environment"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
