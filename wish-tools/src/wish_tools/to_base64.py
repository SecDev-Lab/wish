import base64


def main(plain: str) -> str:
    encoded_bytes = base64.b64encode(plain.encode("utf-8"))
    encoded_str = encoded_bytes.decode("utf-8")
    return encoded_str
