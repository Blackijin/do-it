import ssl, os, sys, socket, http.server, struct, zlib

CERT = 'cert.pem'
KEY  = 'key.pem'
PORT = 8443

def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()

def make_cert(ip):
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime, ipaddress

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Do It App')])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
            x509.IPAddress(ipaddress.IPv4Address(ip)),
        ]), critical=False)
        .sign(key, hashes.SHA256())
    )
    with open(CERT, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(KEY, 'wb') as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        ))

def make_png(size):
    """Generate a solid indigo PNG icon using only stdlib."""
    r, g, b = 0x4f, 0x46, 0xe5  # #4f46e5

    raw = b''
    for _ in range(size):
        raw += b'\x00' + bytes([r, g, b] * size)
    compressed = zlib.compress(raw, 9)

    def chunk(tag, data):
        c = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', c)

    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', compressed)
        + chunk(b'IEND', b'')
    )

def make_icons():
    for size, name in [(192, 'icon-192.png'), (512, 'icon-512.png')]:
        if not os.path.exists(name):
            with open(name, 'wb') as f:
                f.write(make_png(size))

os.chdir(os.path.dirname(os.path.abspath(__file__)))

ip = local_ip()

if not (os.path.exists(CERT) and os.path.exists(KEY)):
    print('  Generating certificate...')
    try:
        make_cert(ip)
        print('  Certificate created.')
    except ImportError:
        print('  ERROR: Run this first:  py -m pip install cryptography')
        sys.exit(1)

make_icons()

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(CERT, KEY)

with http.server.HTTPServer(('0.0.0.0', PORT), http.server.SimpleHTTPRequestHandler) as srv:
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    print(f'\n  PC      ->  https://localhost:{PORT}')
    print(f'  Android ->  https://{ip}:{PORT}')
    print(f'\n  First time on phone: tap Advanced -> Proceed to accept the certificate.')
    print(f'  Press Ctrl+C to stop.\n')
    srv.serve_forever()
