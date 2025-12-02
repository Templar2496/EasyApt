import base64
import os

import pyotp


def new_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="EasyAPT")


def verify(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
