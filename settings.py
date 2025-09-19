import os

# Условный импорт aiogram для совместимости с Windows приложением
try:
    from aiogram.fsm.state import State, StatesGroup
    AIOGRAM_AVAILABLE = True
except ImportError:
    # Создаем заглушки для Windows приложения
    class State:
        def __init__(self):
            pass
    
    class StatesGroup:
        def __init__(self):
            pass
    
    AIOGRAM_AVAILABLE = False

from docx.shared import RGBColor, Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from dotenv import load_dotenv
from enum import IntEnum

load_dotenv()

BUCKET_NAME = "repgen_images"
PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION ="us-central1"

BOT_TOKEN = os.environ.get("BOT_TOKEN")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SQL_USER = os.environ.get("SQL_USER", "postgres")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "password")
SQL_DB = os.environ.get("SQL_DB", "repgen_db")
SQL_HOST = os.environ.get("SQL_HOST", "db")
SQL_PORT = os.environ.get("SQL_PORT", "5432")
PATH_PG_DATA = os.environ.get("PATH_PG_DATA", "./postgres_data")

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 дней

ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

COMMON_DELAY_SECONDS = 2
RATE_DELAY_SECONDS = 3
GPT_MAX_WORKERS = 4
GPT_SEM_COUNT = 1
MODEL_NAME = "gpt-4o-mini"

class DefectStates(StatesGroup):
    uploading = State()
    
class States(IntEnum):
    # Page 1 — Вводная часть
    CHOOSE_JOB_TYPE = 0
    ENTER_OBJECT_NAME = 1
    ENTER_ADDRESS = 2

    # Page 2 — Работы, материалы, расчёты
    SELECT_WORKS = 3
    SELECT_TECH_MATERIALS = 4
    SELECT_CALCULATIONS = 5

    # Page 3 — Конструкции
    SHOW_ADD_MENU = 6
    CHOOSE_CONSTRUCTION_TYPE = 7
    CHOOSE_SUBTYPE = 8
    HANDLE_CUSTOM_INPUT = 9

    # Page 4 — Фото дефектов
    UPLOAD_DEFECT_PHOTO = 10

    # Page 5 — Состояние конструкций
    ADD_STATE_FOR_STRUCTURE = 11
    SHOW_STATE_MENU = 12
    HANDLE_STATE_MENU = 13


JOB_TYPES = {
    "job1": "Комплексное обследование технического состояния",
    "job2": "Обследование технического состояния"
}

JOB_MAPPING = {
    "Комплексное обследование технического состояния": "комплексному обследованию технического состояния",
    "Обследование технического состояния": "обследованию технического состояния"
}

WORK_TYPES = ["Шурфы", "Измерение влажности", "Теплотехнические работы"]
TECH_MATERIALS = ["Бетон", "Металл", "Древесина"]
CALC_TYPES = ["Деревянные конструкции", "Железобетонные конструкции", "Каменные конструкции"]

CONSTRUCTION_STATES = {
    "r": "Работоспособное",
    "o": "Ограниченно-работоспособное",
    "a": "Аварийное"
}

CONSTRUCTION_TREE = {
    "Фундаменты": {
        "Ленточные": {
            "Бутовые": "Фундаменты выполнены ленточными из бутовой кладки",
            "Железобетонные": {
                "Монолитные": "Фундаменты выполнены ленточными монолитными",
                "Сборные": "Фундаменты выполнены ленточными из фундаментных блоков"
            }
        },
        "Свайные": {
            "Деревянные": "Фундаменты выполнены свайными деревянными из бруса",
            "Железобетонные": {
                "__custom__": {
                    "label": "Укажите сечение, мм",
                    "callback": lambda section: (
                        f"Фундаменты выполнены свайными железобетонными, сечением {section} мм"
                    )
                }
            }
        }
    },
    "Стены": {
        "Кирпичные": {
            "__custom__": {
                "label": "Укажите сечение, мм",
                "callback": lambda section: (
                    f"Стены выполнены из кирпичной кладки на цементно-песчаном растворе, толщиной {section} мм"
                )
            }
        },
        "Железобетонные": {
            "__custom__": {
                    "label": "Укажите серию и марку",
                    "callback": lambda series, mark: (
                        f"Стены выполнены из навесных сборных железобетонных панелей марки {mark} по серии {series}"
                    )
            }
        }
    }
}

HEADER_TEXT = "ООО «Невская Проектная Компания»"
FOOTER_TEXT = "Отчёт по обследованию технического состояния здания, расположенного по адресу: "

TITLE_1 = "1.  ВВОДНАЯ ЧАСТЬ"
TITLE_1_1 = "1.1.  Основания и цель проведения работ"
TITLE_1_2 = "1.2.  Характеристика объекта обследования и описание их архитектурно-строительных и инженерных решений."
TITLE_2 = "2.  РЕЗУЛЬТАТЫ ОБСЛЕДОВАНИЯ ОБЪЕКТА"
TITLE_2_1 = "2.1.  Ведомость дефектов и повреждений"
SUBTITLE_2_1 = "выявленных при проведении комплексного обследования технического состояния здания, расположенного по " \
    "адресу:"
TITLE_3 = "3.  ЗАКЛЮЧЕНИЕ ПО ОБСЛЕДОВАНИЮ ТЕХНИЧЕСКОГО СОСТОЯНИЯ ЗДАНИЯ"

BODY_TEXT_1_1 = "Основанием для проведения работ по "
BODY_TEXT_1_2 = " здания "
BODY_TEXT_1_3 = ", расположенного по адресу: "
BODY_TEXT_1_4 = ", (далее по тексту – по обследованию здания) является договор оказания услуг №07-09/21-3 от " \
    "14.09.2021 года между ООО «БС 98 КОНСТРАКШН» и ООО «Невская Проектная Компания»."

ADDITIONAL_BODY_2_TEXT = "Протоколы технического диагностирования материалов строительных конструкций приведены в " \
    "приложении 4 к отчету. "
BODY_TEXT_2_1 = "Обследование здания выполнено в соответствии с программой обследования. Копия программы приведена в " \
    "приложении 2 к отчёту. При проведении работ использованы методики ГОСТ 31937-2011 «Здания и сооружения. Правила " \
    "обследования и мониторинга технического состояния», СП 13-102-2003 «Правила обследования несущих строительных " \
    "конструкций зданий и сооружений», «Пособие по обследованию строительных конструкций зданий» ЦНИИПРОМЗДАНИЙ, М., " \
    "1997 г., а также другие нормативные, технические и методические документы, приведённые в приложении 6 к отчёту. " \
    "Дефекты и повреждения с фотофиксацией наиболее характерных из них, выявленные в ходе проведении обследования, а " \
    "также рекомендации по их устранению сведены в «Ведомость дефектов и повреждений...», представленную в п. 3.1. " \
    "Фотофиксация основных элементов строительных конструкций, их объемно-планировочного расположения и " \
    "архитектурных решений здания приведена в приложении 3 к отчёту. "
BODY_TEXT_2_2 = "Результаты измерительного контроля, графическое отображение объемно-планировочных решений " \
    "строительных конструкций здания представлены на чертежах в приложении 7 к отчёту."

BODY_TEXT_3_1 = "Объект контроля: "
BODY_TEXT_3_2 = "строительные конструкции здания."
BODY_TEXT_3_3 = "Эксплуатирующая организация: "
BODY_TEXT_3_5 = "Дата контроля: "
BODY_TEXT_3_6 = "с 27 сентября по 28 октября 2021 года."

SIGN_TEXT_1 = "«УТВЕРЖДАЮ»"
SIGN_TEXT_2 = "Генеральный директор"
SIGN_TEXT_3 = "ООО «Невская Проектная Компания»"
SIGN_TEXT_4 = "_______________ И.Р. Сорокин"

ALIGN_CENTER = WD_ALIGN_PARAGRAPH.CENTER
ALIGN_LEFT = WD_ALIGN_PARAGRAPH.LEFT
ALIGN_JUSTIFY = WD_ALIGN_PARAGRAPH.JUSTIFY
ALIGN_RIGHT = WD_ALIGN_PARAGRAPH.RIGHT

HEADER_FONT_SIZE = Pt(14)
FOOTER_FONT_SIZE = Pt(10)

FIRST_LINE_INDENT = Cm(1.25)
PAGE_RIGHT_INDENT = Cm(-2)
LANDSCAPE_PAGE_RIGHT_INDENT = Cm(-2)
PAGE_LEFT_INDENT = Cm(-1)
LANDSCAPE_PAGE_LEFT_INDENT = Cm(-1.5)
PAGE_LINE_SPACING = 1.5
LANDSCAPE_PAGE_LINE_SPACING = 1.2
PAGE_SPACE_BEFORE = Pt(12)
LANDSCAPE_PAGE_SPACE_BEFORE = Pt(4)
MAIN_FONT_SIZE = Pt(14)
EXTRA_FONT_SIZE = Pt(12)
TEXT_COLOR = RGBColor(0, 0, 0)

LANDSCAPE_SECTION_WIDTH = 10900000
LANDSCAPE_SECTION_HEIGHT = 7772400
PORTRAIT_SECTION_WIDTH = 7772400
PORTRAIT_SECTION_HEIGHT = 10058400
PAGE_ORIENTATION_LANDSCAPE = WD_ORIENT.LANDSCAPE
PAGE_ORIENTATION_PORTRAIT = WD_ORIENT.PORTRAIT

COMMON_FONT = 'Times New Roman'

CD_TABLE_NUM_COLS = 3
CD_TABLE_NUM_ROWS = 2
CD_TABLE_HEAD_HEIGHT = Cm(1)
CD_TABLE_HEAD_TEXTS = [
    "№ п/п",
    "Позиция",
    "Описание"
]

CD_TABLE_SUBHEAD_HEIGHT = Cm(0.7)
CD_TABLE_SUBHEAD_TEXTS = [
    "Конструктивные решения"
]
CD_TABLE_HEAD_FONT_SIZE = Pt(12)
CD_TABLE_SUBHEAD_FONT_SIZE = Pt(14)
CD_TABLE_COLUMN_WIDTHS = [Cm(2), Cm(4), Cm(20)]


DEFECTS_TABLE_NUM_COLS = 5
DEFECTS_TABLE_NUM_ROWS = 2
DEFECTS_TABLE_HEAD_TEXTS = [
    "№ п/п",
    "Описание дефекта или повреждения",
    "Местоположение дефекта или повреждения",
    "Фотофиксация наиболее характерного дефекта или повреждения",
    "Метод устранения дефекта или повреждения"
]
DEFECTS_TABLE_SUBHEAD_TEXTS = [str(i+1) for i in range(DEFECTS_TABLE_NUM_COLS)]
DEFECTS_TABLE_HEAD_FONT_SIZE = Pt(12)
DEFECTS_TABLE_COLUMN_WIDTHS = [Cm(0.5), Cm(6), Cm(4), Cm(11), Cm(8)]

CONCLUSION_TABLE_NUM_COLS = 4
CONCLUSION_TABLE_NUM_ROWS = 2
CONCLUSION_TABLE_HEAD_FONT_SIZE = Pt(14)
CONCLUSION_TABLE_HEAD_TEXTS = [
    "14.",
    "Результаты оценки технического состояния строительных конструкций объекта",
    "Наименование строительных конструкций",
    "Техническое состояние в соответствии с ГОСТ 31937-2011"
]
CONCLUSION_TABLE_SUBHEAD_TEXTS = [
    "15.",
    "Условия дальнейшей безопасной эксплуатации",
    "",
    "Выполнение мероприятий по устранению дефектов и повреждений в объеме, предусмотренном «Ведомостью дефектов и "
    "повреждений...» (п. 3.1.), и общих рекомендаций, изложенных в «Рекомендациях по результатам обследования» (п.5.)"
]

CONCLUSION_TABLE_COLUMN_WIDTHS = [Cm(0.5), Cm(8), Cm(7), Cm(6)]

# Константы для таблицы износа
WEAR_TABLE_NUM_COLS = 4
WEAR_TABLE_NUM_ROWS = 2
WEAR_TABLE_HEAD_TEXTS = [
    "Элементы жилого здания",
    "Удельный вес элемента в общей стоимости здания, %",
    "Физический износ элементов здания %",
    ""
]
WEAR_TABLE_SUBHEAD_TEXTS = [
    "",
    "",
    "По результатам оценки",
    "Средневзвешенная степень физического износа"
]
WEAR_TABLE_HEAD_FONT_SIZE = Pt(12)
WEAR_TABLE_SUBHEAD_FONT_SIZE = Pt(10)
WEAR_TABLE_COLUMN_WIDTHS = [Cm(8), Cm(4), Cm(4), Cm(4)]

# Стандартные элементы здания для таблицы износа
DEFAULT_WEAR_ELEMENTS = [
    ["Фундаменты", "2", "30", "0.6"],
    ["Стены и перегородки", "29", "20", "5.8"],
    ["Перекрытия", "16", "35", "5.6"],
    ["Кровля", "3", "50", "1.5"],
    ["Полы", "10", "45", "4.5"],
    ["Проёмы", "9", "30", "2.7"],
    ["Отделочные работы", "6", "55", "3.3"],
    ["Внутренние санитарно-технические устройства", "12", "45", "5.4"],
    ["Внутренние электротехнические устройства", "9", "30", "2.7"],
    ["Прочие работы", "4", "45", "1.8"],
    ["Итого", "", "", "32.1"]
]

# Стандартные конструктивные решения
DEFAULT_CONSTRUCTIVE_DECISIONS = [
    ["Фундаменты", "Фундаменты выполнены ленточными из фундаментных блоков"],
    ["Стены", "Стены кирпичные 750"],
    ["Покрытие", "Конструкции покрытия выполнены в виде настила из сборных железобетонных ребристых плит"],
    ["Кровля", "Плоская. Покрытие кровли из рулонных материалов"]
]
