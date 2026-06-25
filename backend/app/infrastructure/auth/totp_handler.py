"""
Handler de TOTP para autenticação em dois fatores (2FA)
"""
import pyotp
import qrcode
import base64
from io import BytesIO


def generate_totp_secret() -> str:
    """Gera um novo segredo TOTP"""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Retorna a URI TOTP para geração do QR Code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="GOAir Monitoramento")


def verify_totp(secret: str, token: str) -> bool:
    """Verifica um token TOTP"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def generate_qr_code_base64(uri: str) -> str:
    """Gera QR Code como string base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
