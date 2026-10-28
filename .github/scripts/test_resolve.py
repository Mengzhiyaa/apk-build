"""Run with: python -m unittest discover -s .github/scripts -p 'test_*.py'."""

import unittest
from resolve import resolve, resolve_benchmark, resolve_publish

SHA = "a" * 40


class ResolveTests(unittest.TestCase):
    def dispatch(self, **payload):
        return resolve({"client_payload": {"sha": SHA, **payload}}, {}, "repository_dispatch")

    def test_automatic_tests_cover_all_backends_on_dev(self):
        result = self.dispatch(ref="dev")
        self.assertEqual((result["backend"], result["ref"], result["release"]), ("all", "dev", "false"))

    def test_each_backend_has_distinct_status(self):
        statuses = {self.dispatch(backend=b)["status_context"] for b in ("all", "runtime", "ty", "pyrefly")}
        self.assertEqual(len(statuses), 4)

    def test_legacy_features_are_not_silently_dropped(self):
        for feature, backend in (("lsp", "runtime"), ("lsp-ty", "ty"), ("lsp-pyrefly", "pyrefly")):
            with self.subTest(feature=feature):
                self.assertEqual(self.dispatch(features=feature)["backend"], backend)

    def test_manual_release(self):
        result = resolve({}, {"source_sha": SHA, "release": True, "release_backend": "pyrefly"}, "workflow_dispatch")
        self.assertEqual((result["backend"], result["release_backend"], result["release"]), ("all", "pyrefly", "true"))

    def test_legacy_release_cannot_bypass_full_tests(self):
        result = resolve({"action": "run-release", "client_payload": {"sha": SHA, "features": "lsp-pyrefly"}}, {}, "repository_dispatch")
        self.assertEqual((result["backend"], result["release_backend"], result["release"]), ("all", "pyrefly", "true"))

    def test_rejects_malformed_dispatch(self):
        for payload in ({"sha": "dev"}, {"sha": SHA + "\n"}, {"ref": "dev\nrelease=true"},
                        {"backend": "all-features"}, {"features": "lsp,lsp-ty"},
                        {"release": "false"}, {"release_backend": "all"}, {"release_channel": "oops"},
                        {"package": "other"}, {"release": True, "backend": "runtime"}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.dispatch(**payload)

    def test_publish_preserves_the_tested_sha_and_backend(self):
        result = resolve_publish({"source_sha": SHA, "backend": "pyrefly", "release_channel": "rc"})
        self.assertEqual((result["sha"], result["release_backend"], result["channel"]), (SHA, "pyrefly", "rc"))

    def test_publish_requires_one_backend(self):
        with self.assertRaises(ValueError):
            resolve_publish({"source_sha": SHA, "backend": "all"})

    def test_reusable_benchmark_ignores_parent_release_payload(self):
        event = {"client_payload": {"sha": "b" * 40, "backend": "all", "release": True}}
        result = resolve_benchmark(event, {"source_sha": SHA, "backend": "runtime", "benchmark_mode": "smoke"})
        self.assertEqual(result, {"sha": SHA, "ref": "main", "backend": "runtime", "mode": "smoke"})

    def test_standalone_benchmark(self):
        result = resolve_benchmark({"client_payload": {"sha": SHA, "backend": "pyrefly"}}, {})
        self.assertEqual((result["mode"], result["backend"]), ("performance", "pyrefly"))

    def test_invalid_benchmark(self):
        for inputs in ({"source_sha": SHA, "backend": "all"}, {"source_sha": SHA, "benchmark_mode": "invalid"}):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                resolve_benchmark({}, inputs)


if __name__ == "__main__":
    unittest.main()
