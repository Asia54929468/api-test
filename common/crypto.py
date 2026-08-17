import secrets
from nacl.bindings import (
    crypto_box_keypair,
    crypto_box_beforenm,
    crypto_box_afternm,
)


def encrypt(content: str, public_key: str) -> str:
    """
    :param content: 要加密的明文
    :param public_key: 接收方公钥，十六进制字符串
    :return: nonce + 临时公钥 + 密文，最终以十六进制字符串返回
    """

    # C++ 中的 QByteArray::fromHex(publicKey.toLatin1())
    recipient_public_key = bytes.fromhex(public_key)

    # 生成临时密钥对
    ephemeral_public_key, ephemeral_secret_key = crypto_box_keypair()

    # 计算共享密钥，对应 crypto_box_beforenm
    shared_key = crypto_box_beforenm(
        recipient_public_key,
        ephemeral_secret_key,
    )

    # C++ 中使用 content.toLocal8Bit()
    # 通常 Python 使用 UTF-8；如果必须完全匹配系统本地编码，需要改成对应编码
    message = content.encode("utf-8")

    # crypto_box_afternm 内部会完成与 crypto_box_ZEROBYTES /
    # crypto_box_BOXZEROBYTES 等价的填充和裁剪。
    nonce = secrets.token_bytes(24)
    ciphertext = crypto_box_afternm(
        message,
        nonce,
        shared_key,
    )

    # 对应：
    # randomBuf + pubkey + c.constData() + crypto_box_BOXZEROBYTES
    result = nonce + ephemeral_public_key + ciphertext

    return result.hex()