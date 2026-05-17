# Dahua Cube A1 Integration for Home Assistant

Custom integration for Dahua Cube A1 (DH-C3A / DH-C5A) cameras using the native Dahua SDK.

## Installation via HACS (recommended)

1. Open **HACS → Integrations → ⋮ → Custom repositories**
2. Add the repository:
   - **Repository**: `jabenetti/dahua_cube_a1`
   - **Category**: `Integration`
3. Click **Add**
4. Search for **Dahua Cube A1** in HACS and install it
5. Restart Home Assistant

The Dahua SDK will be installed automatically together with Flask and Flask-HTTPAuth.

## Features

- Full event streaming (SmartMotionHuman, etc.) via CGI proxy
- Digest authentication (exact match with original Dahua CGI)
- Support for multiple cameras on the same proxy port
- Keep-alive multipart responses
- Local push notifications to Home Assistant

## Support

- [Issues](https://github.com/jabenetti/dahua_cube_a1/issues)
- [Discussions](https://github.com/jabenetti/dahua_cube_a1/discussions)