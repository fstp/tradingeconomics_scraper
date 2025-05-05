import base64
import json
import zlib
from typing import Any, Dict

from nacl.secret import SecretBox

TEdecryptk = "j9ONifjoKzxt7kmfYTdKK/5vve0b9Y1UCj/n50jr8d8="
TEdecryptn = "Ipp9HNSfVBUntqFK7PrtofYaOPV312xy"


def _base64_to_bytes(base64_string):
    """Converts a Base64 string to a bytes object."""
    return base64.b64decode(base64_string)


def decrypt_base64_message(ciphertext: str) -> Dict[str, Any]:
    """Decrypts a ciphertext base64 string using the provided key and nonce."""
    key = _base64_to_bytes(TEdecryptk)
    nonce = _base64_to_bytes(TEdecryptn)
    box = SecretBox(key)
    decrypted_plaintext = box.decrypt(base64.b64decode(ciphertext), nonce)
    decrypted_plaintext = zlib.decompress(decrypted_plaintext).decode("utf-8")
    return json.loads(decrypted_plaintext)


def decrypt_binary_message(ciphertext: bytes) -> Dict[str, Any]:
    """Decrypts a ciphertext in bytes using the provided key and nonce."""
    key = _base64_to_bytes(TEdecryptk)
    nonce = _base64_to_bytes(TEdecryptn)
    box = SecretBox(key)
    decrypted_plaintext = box.decrypt(ciphertext, nonce)
    decrypted_plaintext = zlib.decompress(decrypted_plaintext).decode("utf-8")
    return json.loads(decrypted_plaintext)


def _test():
    """Example usage"""
    base64_ciphertext = "dDrAMoet7QgrKT+VuxPmJfMomHrDL9TK3q+P1muoRzhndFsl478ONrcK6AFMXyCZiFosqEWxSOtzj0NhKVGXbSa8nCvZqHYbSmYa+hoRICqIVbbiGGe1/nuI7U80NU/ZTS0s9rMrCjqdAAwFI8b+LaDJyp4zxJNTWtLPTDuMuqw5TU5XtPk/PytY3zOlsb+snJhgWFuj17nXMtYJIb+QA3CJU4oD9x9wWACnUa7NAB9vuWiA8X+6UM4mx17bg1TFrFIm3anjleCSg+DKWLStP6XHauEwWhWouzxvj/4il02Ycw13khAvTKmeTsRadOm/NyOev5rOuMIT4rAQzO2ipd538A4z7iR+YkROckkYQW+hM1/VKSftV9nBVFp2/avS53lpZwGBuJScaOt4ynli1wlqsl6K8M7opthvgnNs04L/DkQ/FjTLoWQzdtwWt50sToIdRsjSdc/H8kQXlbuH5eRlOMZrw9ZF1OzBwv5CLYIRfIkmZwOGb+Ns6cAkI745of3w/2bV7L/8pMkV3N+lG9VQ/m6jkr8KzhKspA2WSXFtIjDlBaddtFIIUwtaCnT0f66MmDtexuHFXucoaoSibms8RBVTcbyDQj5oZx1pRCsBUbbyPv8bmnWlO+iYYSTuQw=="

    decrypted_data = decrypt_base64_message(base64_ciphertext)
    if decrypted_data:
        print(json.dumps(decrypted_data, indent=4))
