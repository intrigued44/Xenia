import asyncio
import os
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.storage import StorageFile

async def extract_text_from_image(image_path):
    try:
        # Resolve absolute path for StorageFile
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            return ""
            
        engine = OcrEngine.try_create_from_language(Language("en-US"))
        if engine is None:
            engine = OcrEngine.try_create_from_user_profile_languages()
            if engine is None:
                return ""
                
        file = await StorageFile.get_file_from_path_async(abs_path)
        stream = await file.open_async(0) # FileAccessMode.Read
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        
        result = await engine.recognize_async(bitmap)
        return result.text
    except Exception as e:
        import logging
        logging.error(f"OCR Error: {e}", exc_info=True)
        return ""

def extract_text_sync(image_path):
    """Synchronous wrapper for OCR extraction."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        text = loop.run_until_complete(extract_text_from_image(image_path))
        loop.close()
        return text
    except Exception:
        return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = extract_text_sync(sys.argv[1])
        print("--- EXTRACTED TEXT ---")
        print(text)
