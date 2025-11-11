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


class MarkVolumeUnit(enum.Enum):
    """Единицы измерения объема дефекта"""
    m2 = "m2"
    m3 = "m3"
    pog_m = "pog_m"
    mm = "mm"
    pcs = "pcs"