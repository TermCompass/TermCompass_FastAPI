import base64
import zlib

# zlib으로 압축된 base64문자를 압축 해체

def decompress_data(compressed_content: str) -> bytes:
    compressed_data = base64.b64decode(compressed_content)
    decompressed_data = zlib.decompress(compressed_data)
    return decompressed_data