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

## License

MIT