import enum

class GlobalRoleType(enum.Enum):
    """Типы глобальных ролей пользователей"""
    user = "user"
    admin = "admin"

class RoleType(enum.Enum):
    """Типы ролей пользователей (группы)"""
    sr = "sr"
    npk = "npk"
    all = "all"

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


class DefectType(enum.Enum):
    """Типы дефектов"""
    concrete_reinforcement = "concrete_reinforcement"
    concrete_destruction = "concrete_destruction"
    leak_traces = "leak_traces"
    efflorescence = "efflorescence"
    brick_cracks = "brick_cracks"
    brick_destruction = "brick_destruction"
    concrete_cracks = "concrete_cracks"
    soil_vegetation = "soil_vegetation"
    anticorrosion_destruction = "anticorrosion_destruction"
    finishing_destruction = "finishing_destruction"
    element_bends = "element_bends"
    mechanical_deform = "mechanical_deform"
    non_project_holes = "non_project_holes"
    emergency_section = "emergency_section"


class DefectCategory(enum.Enum):
    """Категории дефектов (A, B, C)"""
    A = "A"
    B = "B"
    C = "C"