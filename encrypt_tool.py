#!/usr/bin/env python3
import sys
import os
from pathlib import Path


def encrypt_plugin(input_path: str, output_path: str):
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
    except ImportError:
        print("Ошибка: установите pycryptodome → pip install pycryptodome")
        sys.exit(1)

    # ДОЛЖЕН СОВПАДАТЬ С КЛЮЧОМ В plugin_loader.py
    SECRET_KEY = b'PrisonToolkitKey1234567890ABCDEF'

    with open(input_path, 'rb') as f:
        source_code = f.read()

    cipher = AES.new(SECRET_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(source_code)

    with open(output_path, 'wb') as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    print(f"Успешно зашифровано: {Path(output_path).name}")
    print(f"  Исходный размер: {os.path.getsize(input_path)} байт")
    print(f"  Зашифрованный размер: {os.path.getsize(output_path)} байт")
    print(
        f"\nТеперь удалите {input_path} и распространяйте только {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python encrypt_tool.py исходник.py плагин.enc")
        print("Пример: python encrypt_tool.py plugins/dead_zone.py plugins/dead_zone.enc")
        sys.exit(1)

    encrypt_plugin(sys.argv[1], sys.argv[2])
