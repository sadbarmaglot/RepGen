# UI компоненты Windows приложения
# Импорты выполняются по требованию для лучшей производительности

# Экспорт основных компонентов
from .main_window import DefectAnalyzerWindow

# Диалоги (импортируются по требованию для избежания ошибок зависимостей)
try:
    from .project_dialogs import ProjectDialog, ProjectManagerDialog
except ImportError:
    pass

try:
    from .wear_calculator_dialog import WearCalculatorDialog
except ImportError:
    pass

try:
    from .cloud_sync_dialog import CloudSyncDialog
except ImportError:
    pass

try:
    from .model_3d_dialog import Model3DDialog
except ImportError:
    pass