import enum

class GlobalRoleType(enum.Enum):
    """Типы глобальных ролей пользователей"""
    user = "user"
    admin = "admin"

class RoleType(enum.Enum):
    """Типы ролей пользователей (группы)"""
    sr = "sr"
    npk = "npk"
    apa = "apa"
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
    emergency_section = "emergency_section"
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
    bio_corrosion_wood = "bio_corrosion_wood"
    masonry_joint_weathering = "masonry_joint_weathering"
    floor_flooding = "floor_flooding"
    non_compliance = "non_compliance"
    structural_collapse = "structural_collapse"
    joint_damage = "joint_damage"
    vent_grille_damage = "vent_grille_damage"
    gate_damage = "gate_damage"
    door_damage = "door_damage"
    engineering_network_damage = "engineering_network_damage"
    roof_damage = "roof_damage"
    porch_damage = "porch_damage"
    stairway_damage = "stairway_damage"
    blind_area_damage = "blind_area_damage"
    window_damage = "window_damage"
    foundation_damage = "foundation_damage"
    oil_contamination = "oil_contamination"
    support_zone_destruction = "support_zone_destruction"
    wood_destruction = "wood_destruction"
    slab_joint_destruction = "slab_joint_destruction"
    floor_destruction = "floor_destruction"
    material_storage = "material_storage"
    through_corrosion = "through_corrosion"
    through_hole = "through_hole"
    layered_corrosion = "layered_corrosion"
    fungal_growth = "fungal_growth"
    fire_traces = "fire_traces"
    floor_cracks = "floor_cracks"
    wood_cracks = "wood_cracks"
    plaster_cracks = "plaster_cracks"
    finishing_loss = "finishing_loss"
    structural_absence = "structural_absence"
    pitting_corrosion = "pitting_corrosion"


class DefectCategory(enum.Enum):
    """Категории дефектов (A, B, C)"""
    A = "A"
    B = "B"
    C = "C"


class ObjectStatus(enum.Enum):
    """Статусы объекта"""
    not_started = "not_started"  # не начат
    in_progress = "in_progress"  # в работе
    completed = "completed"      # выполнено