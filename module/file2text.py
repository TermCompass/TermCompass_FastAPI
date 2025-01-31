from io import BytesIO
from fastapi import UploadFile
from pdfminer.high_level import extract_text

async def file2text(file: UploadFile):
    if file.content_type == "application/pdf":
        content = await file.read()
        result = extract_text(BytesIO(content))
        print("result", result)
        return result    
    
    elif file.content_type == "application/x-hwp":
        pass

    else:
        raise TypeError('PDF,HWP파일인지 확인해주세요.')
    