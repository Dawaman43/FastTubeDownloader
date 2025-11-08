#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIV = ROOT / 'dev_keys' / 'fasttube_extension_private.pem'
DEFAULT_MANIFEST = ROOT / 'manifest.json'


def have_openssl() -> bool:
    try:
        subprocess.run(['openssl', 'version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def ensure_private_key(path: Path, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return
    if not have_openssl():
        print('ERROR: openssl not found. Please install openssl and retry.', file=sys.stderr)
        sys.exit(2)
    subprocess.run(['openssl', 'genrsa', '-out', str(path), '2048'], check=True)


def get_public_der_from_private(path: Path) -> bytes:
    if not have_openssl():
        print('ERROR: openssl not found. Please install openssl and retry.', file=sys.stderr)
        sys.exit(2)
    proc = subprocess.run(['openssl', 'rsa', '-in', str(path), '-pubout', '-outform', 'DER'], check=True, capture_output=True)
    if proc.stdout:
        return proc.stdout
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(['openssl', 'rsa', '-in', str(path), '-pubout', '-outform', 'DER', '-out', str(tmp_path)], check=True)
        data = tmp_path.read_bytes()
        return data
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def base64_noline(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def chrome_id_from_pubkey_der(der: bytes) -> str:
    digest = hashlib.sha256(der).digest()
    first16 = digest[:16]
    alphabet = 'abcdefghijklmnop'
    chars = []
    for b in first16:
        hi = (b >> 4) & 0xF
        lo = b & 0xF
        chars.append(alphabet[hi])
        chars.append(alphabet[lo])
    return ''.join(chars)


def patch_manifest(manifest_path: Path, key_b64: str, dry_run: bool) -> None:
    data = json.loads(manifest_path.read_text())
    old_key = data.get('key')
    data['key'] = key_b64
    if dry_run:
        print('DRY-RUN: Would set manifest.key (length={} chars).'.format(len(key_b64)))
        if old_key and old_key != key_b64:
            print('DRY-RUN: Existing key differs and would be replaced.')
        return
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--private', type=Path, default=DEFAULT_PRIV, help='Path to RSA private key (PEM). Will be created if missing.')
    ap.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST, help='Path to manifest.json to patch.')
    ap.add_argument('--overwrite', action='store_true', help='Regenerate the private key (changes extension ID!).')
    ap.add_argument('--dry-run', action='store_true', help='Do not modify manifest.json, just print info.')
    args = ap.parse_args()

    if not args.manifest.exists():
        print(f'ERROR: manifest.json not found at {args.manifest}', file=sys.stderr)
        sys.exit(1)

    ensure_private_key(args.private, overwrite=args.overwrite)
    pub_der = get_public_der_from_private(args.private)
    key_b64 = base64_noline(pub_der)
    ext_id = chrome_id_from_pubkey_der(pub_der)

    patch_manifest(args.manifest, key_b64, dry_run=args.dry_run)

    print('OK: Generated/loaded private key at:', args.private)
    print('OK: Derived public key Base64 length:', len(key_b64))
    print('Extension ID:', ext_id)
    print('\nNext:')
    print('  1) Reload the unpacked extension in chrome://extensions')
    print('  2) Re-run ./setup.sh and enter this Extension ID when prompted, so native host permissions match')

if __name__ == '__main__':
    main()
