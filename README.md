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

## Test and release orchestration

The APK source repository dispatches **Test APK** for pushes to `main` and
`dev`, same-repository pull requests, and manual runs. The request contains a
full source `sha`, a reporting `ref`, and `backend` (`all`, `runtime`, `ty`, or
`pyrefly`). Automatic runs use `all`. `.github/scripts/resolve.py` validates
requests before scheduling tests; legacy `features` values remain accepted.
The source and infrastructure changes must be deployed together. Deploy this
repository's default branch first, then push the source changes to `main` or
`dev`; tested source SHAs must contain the new CI recipes and setup action.

The original `test.yml` entry point runs reusable `test-suite.yml` and reports
`apk-build / tests`. The original `test-linux.yml`, `test-macos.yml` and
`test-windows.yml` remain active platform jobs, grouped by `test-kernel.yml`
for each backend.
Focused manual runs use `apk-build / tests (BACKEND)` so they cannot overwrite
the all-backend gate. Each check also reports its own result and a job summary.
Required failures, unexpected skips and cancellations prevent a passing gate.

| Check | Coverage |
| --- | --- |
| Kernel | Separate runtime/ty/Pyrefly jobs on Linux, macOS and Windows, CPython 3.13; selected engine tests, all kernel session suites and Clippy |
| Quality | Rust formatting, actionlint in both repositories, dispatch contract tests |
| Python helpers | Complete standalone pytest suite, once on Linux; Polars, Ibis/DuckDB, and PyArrow required; skipped cases fail the gate |
| ABI/runtime | Supported CPython 3.8–3.15, with native architecture checks |
| Debugger | Linux CPython 3.8–3.15 plus macOS/Windows 3.13; callback and shutdown gates included |
| Benchmark smoke | Functional quick suite and three-platform notebook/background smoke |

Commands and backend-to-feature mapping belong to the checked-out APK source's
`justfile`. `.github/actions/setup-test` and `scripts/ci/requirements.txt` in that
source install the common environment. Dependencies are installed before the
complete kernel suite, eliminating the old optional-dependency reruns. Clippy
and tests run as separate steps, so a lint failure is distinguishable from a
test failure. Each leaf job name includes its backend, platform, Python version
and purpose; caller names are not required to identify a job in the sidebar.
Cargo uses `--locked`; backend-specific caches are separate. Console, notebook and
background tests keep their own processes. ABI checks do not multiply by backend.
Quality checks install the pinned actionlint binary from its official GitHub
release and verify its published SHA-256 checksum. The Rust tool installer is
used only for Rust tools. Interpreter-only setup disables uv's package cache,
so a missing package cache cannot fail otherwise successful debugger jobs.
Only the runtime backend saves the shared uv cache for each OS/Python version;
other backends and helper jobs only restore it. Source setup selects matching
Homebrew LLVM/libclang tools for macOS binding generation without changing the
runner's native compiler. `libpy-check` requires bindgen 0.73.2 or newer in the
0.73 series, including the struct-definition fix for Clang 22 and later.

The helper job enables `python-helper-dependencies` in the source setup action
and installs `scripts/ci/requirements-helpers.txt` in addition to the base
dependencies. This profile includes Polars, Ibis with its DuckDB execution
backend, DuckDB connection support, and PyArrow. It runs
`just python-helpers-ci`, which requires these imports and the checked-in
`crates/apk/tests/fixtures/data_explorer_parity.json` before collection. Any
skipped helper case fails this job; skip reasons remain visible in the log and
`python-helpers-SOURCE_SHA` contains the JUnit report when pytest produces one.
The fixture is generated explicitly from a recorded Positron revision using the
source repository's `scripts/ci/generate_data_explorer_fixture.py`; CI consumes
that reference without downloading Positron or generating expectations from APK.
Kernel jobs retain the common dependency profile, and interpreter-only jobs
continue to install no optional data backends.

A release request adds `release: true`, `release_backend` (default `ty`) and
`release_channel` (`alpha`, `beta`, `rc`, `stable`). Releases require
`backend: all`. After the exact SHA passes the gate, the original `release.yml`
builds and publishes the selected backend through its original platform workflows. Manual
**Build APK Release** runs and legacy `run-release` events run the same complete
suite before any release build. Internal Test APK calls reuse their completed
gate for that SHA instead of repeating the suite. The `release-publish.yml`
helper remains available for existing callers and delegates to `release.yml`.
Source commit-message release tags apply only to `main`, so `dev` pushes trigger
tests only.

Ty retains canonical release tags and filenames. Other backends append
`-runtime` or `-pyrefly` to the tag/archive version, preventing download and tag
collisions. Release status contexts include the backend. Failed publication
never deletes a pre-existing release or tag.

Full performance measurements are separate from the required smoke checks.
The **Benchmark APK** workflow accepts one backend per run and includes the
backend in its cache, artifact names and performance status.

To check orchestration locally:

```sh
actionlint
python -m unittest discover -s .github/scripts -p 'test_*.py'
```

## CPython ABI Matrix

The test workflow includes a blocking pybridge matrix for CPython 3.8–3.15.
For Python 3.8–3.13 it compiles a temporary probe against each selected
installation's `Python.h` and compares `PyConfig` size, alignment, and field
offsets with APK's checked-in ABI table. It then runs the real pybridge
initialization tests against the matching shared library. Python 3.14 and 3.15
exercise the opaque `PyInitConfig` backend instead.

Every versioned Unix 64-bit and Windows 64-bit table entry is checked. Separate
Linux, macOS, and Windows ARM64 jobs cover the native release architectures.
The retained 32-bit tables are not currently part of the CI matrix; a future
32-bit runner can enable the same verifier without changing its test code.

## libpy Runtime Matrix

The libpy workflow runs every supported Python version (3.8–3.15) on Linux,
macOS, and Windows. Each job loads and initializes the selected interpreter in
the Rust process, verifies its executable and path configuration, creates a
Matplotlib figure through APK's embedded backend, exercises the console plot
comm pipeline, and verifies notebook PNG display data. All supported release
interpreters are blocking, including Python 3.8–3.9 on Linux, macOS and Windows.
Python 3.7 remains a non-blocking Linux-only diagnostic. Free-threaded and
embeddable Windows distributions run as supplemental diagnostics.

## License

MIT
