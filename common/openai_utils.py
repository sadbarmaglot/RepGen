import json
import uuid

from openai import OpenAI

from common.gc_utils import upload_to_gcs
from common.defects_db import SYSTEM_PROMPT, USER_PROMPT

client = OpenAI()

async def process_photo(photo_file, context):
    uid = str(uuid.uuid4())[:8]
    filename = f"defect_{uid}.jpg"
    await photo_file.download_to_drive(filename)
    blob, image_url = await upload_to_gcs(filename, ".jpg")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                SYSTEM_PROMPT,
                {"role": "user", "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        context.user_data.setdefault("Page4", {}).setdefault("defects", []).append({
            "defect": result["defect_description"],
            "eliminating_method": result["recommendation"],
            "image_path": filename
        })

    except Exception as e:
        print(f"[ERROR] Ошибка при анализе фото: {e}")
    finally:
        blob.delete()