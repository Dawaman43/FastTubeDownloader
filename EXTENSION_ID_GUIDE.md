Permanent extension ID (free, local)

Follow these steps once to generate a private key and use the same extension ID everywhere when loading unpacked.

Linux/macOS:

1) Generate a 2048-bit RSA private key

```bash
openssl genrsa -out myextension_private.pem 2048
```

2) Convert to Base64 PKCS#8 for manifest.json

```bash
openssl pkcs8 -topk8 -inform PEM -outform DER -in myextension_private.pem -nocrypt | base64 -w 0
```

3) Edit manifest.json and paste into the "key" field

```json
"key": "PASTE_BASE64_KEY_HERE"
```

Windows (PowerShell with OpenSSL available, e.g. via Git for Windows):

```powershell
openssl genrsa -out myextension_private.pem 2048
openssl pkcs8 -topk8 -inform PEM -outform DER -in myextension_private.pem -nocrypt | openssl base64 -A
```

Notes
- The key must be a single long Base64 line.
- Do not commit your real private key to a public repo; keep it private.
- The extension ID is derived from the public key; with a fixed key, the ID remains constant across machines.

Updating setup.sh
- After you load the unpacked extension once, copy its ID (chrome://extensions) and re-run ./setup.sh. Provide that ID when prompted so the native host is allowed to talk to your extension.

Troubleshooting
- If Chrome says the key is invalid, ensure you used PKCS#8 DER and Base64 without line breaks.
- If your extension ID changes, Chrome may be ignoring the key field; re-load unpacked after saving manifest.json.
