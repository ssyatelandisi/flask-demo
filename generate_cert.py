from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    serialize_key_and_certificates,
)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta, timezone
from typing import cast
import ipaddress
import pathlib


def create_rootca_key():
    # 生成CA根证书的密钥
    rootCA_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    # 保存CA私钥
    with open("rootCA.key", "wb") as f:
        f.write(
            rootCA_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print("完成CA私钥生成")
    return rootCA_key


def create_rootca_cert(rootCA_key):
    ca_subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "github"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "CA"),
        ]
    )

    # 生成自签名证书
    rootCA_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(issuer)
        .public_key(rootCA_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=10 * 365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(rootCA_key, hashes.SHA256(), default_backend())
    )

    # 保存CA证书
    with open("rootCA.crt", "wb") as f:
        f.write(rootCA_cert.public_bytes(encoding=serialization.Encoding.PEM))
    print("完成CA根证书生成")
    return rootCA_cert


def create_server_key():
    # 生成服务器的私钥
    server_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    # 保存签发的证书
    with open("server.key", "wb") as f:
        f.write(
            server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print("完成服务器私钥生成")
    return server_key


subject_alt_names = {
    "dns_names": ["localhost"],
    "ip_addresses": [
        "127.0.0.1",
    ]
    + [f"192.168.0.{i}" for i in range(1, 255)],  # 内网IP
}


def create_server_csr(server_key):
    # 生成证书签名请求(CSR)
    server_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "github"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Server"),
        ]
    )
    # 添加Subject Alternative Names (SAN) 选项
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(server_subject)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(name) for name in subject_alt_names["dns_names"]]
                + [
                    x509.IPAddress(ipaddress.IPv4Address(ip))
                    for ip in subject_alt_names["ip_addresses"]
                ]
            ),
            critical=False,
        )
        .sign(server_key, hashes.SHA256(), default_backend())
    )

    # 保存CSR
    with open("server.csr", "wb") as f:
        f.write(csr.public_bytes(encoding=serialization.Encoding.PEM))
    print("完成服务器CSR生成")
    return csr


def create_client_csr(server_key):
    # 生成证书签名请求(CSR)

    client_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Shanghai"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "github"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Client"),
        ]
    )
    # 添加Subject Alternative Names (SAN) 选项
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(client_subject)
        .sign(server_key, hashes.SHA256(), default_backend())
    )

    # 保存CSR
    with open("client.csr", "wb") as f:
        f.write(csr.public_bytes(encoding=serialization.Encoding.PEM))
    print("完成客户端CSR生成")
    return csr


def create_server_cert(rootCA_key, rootCA_cert, csr):
    # 使用根证书签发TLS证书
    not_valid_before = datetime.now(timezone.utc)
    not_valid_after = not_valid_before + timedelta(days=365 * 10)  # 1年有效期

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(rootCA_cert.issuer)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(name) for name in subject_alt_names["dns_names"]]
                + [
                    x509.IPAddress(ipaddress.IPv4Address(ip))
                    for ip in subject_alt_names["ip_addresses"]
                ]
            ),
            critical=False,
        )
        .sign(rootCA_key, hashes.SHA256(), default_backend())
    )

    # 使用根CA证书和私钥签发TLS证书

    with open("server.crt", "wb") as f:
        f.write(server_cert.public_bytes(encoding=serialization.Encoding.PEM))
    print("完成服务器证书生成")


def create_client_key() -> rsa.RSAPrivateKey:
    # 生成客户端私钥
    client_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    # 保存CA私钥
    with open("client.key", "wb") as f:
        f.write(
            client_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print("完成客户端私钥生成")
    return client_key


def create_client_cert(rootCA_key, rootCA_cert, csr):
    # 使用根证书签发客户端证书
    not_valid_before = datetime.now(timezone.utc)
    not_valid_after = not_valid_before + timedelta(days=365 * 10)  # 1年有效期

    client_cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(rootCA_cert.issuer)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(rootCA_key, hashes.SHA256(), default_backend())
    )

    # 使用根CA证书和私钥签发客户端证书

    with open("client.crt", "wb") as f:
        f.write(client_cert.public_bytes(encoding=serialization.Encoding.PEM))
    print("完成客户端证书生成")
    return client_cert


if __name__ == "__main__":
    if pathlib.Path("rootCA.key").is_file():
        with open("rootCA.key", "rb") as f:
            rootCA_key = serialization.load_pem_private_key(
                f.read(),
                password=None,  # 如果私钥是加密的，这里需要提供密码
                backend=default_backend(),
            )
    else:
        rootCA_key = create_rootca_key()
    if pathlib.Path("rootCA.crt").is_file():
        with open("rootCA.crt", "rb") as f:
            rootCA_cert = x509.load_pem_x509_certificate(
                f.read(),
                backend=default_backend(),
            )
    else:
        rootCA_cert = create_rootca_cert(rootCA_key)
    if pathlib.Path("server.key").is_file():
        with open("server.key", "rb") as f:
            server_key = serialization.load_pem_private_key(
                f.read(),
                password=None,  # 如果私钥是加密的，这里需要提供密码
                backend=default_backend(),
            )
    else:
        server_key = create_server_key()
    if pathlib.Path("server.csr").is_file():
        with open("server.csr", "rb") as f:
            server_csr = x509.load_pem_x509_csr(
                f.read(),
                backend=default_backend(),
            )
    else:
        server_csr = create_server_csr(server_key)
    if pathlib.Path("server.pem").is_file():
        ...
    else:
        create_server_cert(rootCA_key, rootCA_cert, server_csr)
    if pathlib.Path("client.key").is_file():
        with open("client.key", "rb") as f:
            client_key = cast(
                rsa.RSAPrivateKey,
                serialization.load_pem_private_key(
                    f.read(),
                    password=None,  # 如果私钥是加密的，这里需要提供密码
                    backend=default_backend(),
                ),
            )
    else:
        client_key = create_client_key()
    if pathlib.Path("client.csr").is_file():
        with open("client.csr", "rb") as f:
            server_csr = x509.load_pem_x509_csr(
                f.read(),
                backend=default_backend(),
            )
    else:
        client_csr = create_client_csr(client_key)
    if pathlib.Path("client.crt").is_file():
        with open("client.crt", "rb") as f:
            client_cert = x509.load_pem_x509_certificate(
                f.read(),
                backend=default_backend(),
            )
    else:
        client_cert = create_client_cert(rootCA_key, rootCA_cert, client_csr)
    # 打包成 PKCS#12 (.p12) 文件
    p12_data = serialize_key_and_certificates(
        name=b"Client Certificate",
        key=client_key,
        cert=client_cert,
        cas=[rootCA_cert],  # 可选的 CA 证书链
        # cas=None,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # 保存 .p12 文件
    with open("client.p12", "wb") as p12_file:
        p12_file.write(p12_data)

    print("PKCS#12 (.p12) 文件已生成: client.p12")
