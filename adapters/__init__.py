# Адаптеры для Windows версии
# Импорты выполняются по требованию, чтобы избежать ошибок инициализации

# Основные адаптеры
from .file_manager import WindowsFileManager

# AI адаптеры (требуют OpenAI API)
try:
    from .ai_adapter import analyze_local_photo, batch_analyze_photos, get_openai_client
except ImportError:
    pass

# Дополнительные адаптеры
try:
    from .docx_adapter import create_simple_defects_report
except ImportError:
    pass

try:
    from .wear_calculator import WearCalculator, BuildingTypeTemplates
    from .wear_report_generator import generate_wear_report
except ImportError:
    pass

try:
    from .cloud_sync import CloudSyncManager, CloudSyncConfig
except ImportError:
    pass

# 3D анализ (требует дополнительные зависимости)
try:
    from .model_3d_analyzer import Model3DAnalyzer
except ImportError:
    pass