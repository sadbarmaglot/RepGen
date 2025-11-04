import enum

class GlobalRoleType(enum.Enum):
    """Типы глобальных ролей пользователей"""
    user = "user"
    admin = "admin"

class MarkType(enum.Enum):
    """Типы отметок"""
    defect = "defect"
    overview = "overview"
    exposure = "exposure"
    measurement = "measurement"
    other = "other"
