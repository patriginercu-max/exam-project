"""密码派生与不透明会话令牌。

只使用标准库，避免在 Docker 构建期引入需要编译的依赖。
"""

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """返回 ``算法$迭代次数$盐$派生值`` 形式的字符串。"""
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "{}${}${}${}".format(_ALGORITHM, _ITERATIONS, salt.hex(), derived.hex())


def verify_password(password: str, stored: str) -> bool:
    """用常量时间比较校验明文密码。"""
    try:
        algorithm, iterations, salt_hex, derived_hex = stored.split("$")
        if algorithm != _ALGORITHM:
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (AttributeError, TypeError, ValueError):
        return False
    return hmac.compare_digest(derived.hex(), derived_hex)


def new_session_token() -> str:
    """生成不可猜测的会话标识。权限只由它对应的服务端会话决定。"""
    return secrets.token_urlsafe(32)
