# apk-build

Build and release infrastructure for [APK — A Python Kernel](https://github.com/Mengzhiyaa/apk-build/releases).

## Downloads

Download the latest APK binary from the [Releases](https://github.com/Mengzhiyaa/apk-build/releases) page.

| Platform | Architecture | File |
|----------|-------------|------|
| Linux | x64 | `apk-VERSION-linux-x64.zip` |
| Linux | arm64 | `apk-VERSION-linux-arm64.zip` |
| macOS | Apple Silicon | `apk-VERSION-darwin-arm64.zip` |
| macOS | Intel | `apk-VERSION-darwin-x64.zip` |
| macOS | Universal | `apk-VERSION-darwin-universal.zip` |
| Windows | x64 | `apk-VERSION-windows-x64.zip` |
| Windows | arm64 | `apk-VERSION-windows-arm64.zip` |

## Quick Start

```bash
# Download and extract (example: Linux x64)
unzip apk-*-linux-x64.zip

# Install kernel spec (registers APK with Jupyter)
./apk --install

# Use with Jupyter
jupyter console --kernel=apk
```

## CPython ABI Matrix

The test workflow includes a blocking pybridge matrix for CPython 3.8–3.14.
For Python 3.8–3.13 it compiles a temporary probe against each selected
installation's `Python.h` and compares `PyConfig` size, alignment, and field
offsets with APK's checked-in ABI table. It then runs the real pybridge
initialization tests against the matching shared library. Python 3.14 exercises
the opaque `PyInitConfig` backend instead.

Every versioned Unix 64-bit and Windows 64-bit table entry is checked. Separate
Linux, macOS, and Windows ARM64 jobs cover the native release architectures.
The retained 32-bit tables are not currently part of the CI matrix; a future
32-bit runner can enable the same verifier without changing its test code.

## License

MIT
