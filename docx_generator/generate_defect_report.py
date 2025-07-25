from io import BytesIO
from docx import Document
from docx.enum.section import WD_ORIENT

from docx_generator.docx_utils import defects_table
from settings import (
    DEFECTS_TABLE_NUM_COLS,
    DEFECTS_TABLE_NUM_ROWS,
)

def generate_defect_only_report(user_data: dict) -> BytesIO:
    doc = Document()

    defects = [
        [
            row.get("defect", ""),
            "",
            row.get("image_path", ""),
            row.get("eliminating_method", "")
        ]
        for row in user_data.get("defects", [])
    ]

    if defects:
        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width

        defects_table(doc, defects, DEFECTS_TABLE_NUM_COLS, DEFECTS_TABLE_NUM_ROWS)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
