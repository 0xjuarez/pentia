"""Tests for core.validation — the argument-injection barrier (4.0.1).

A target / URL / model name that reaches a scanner binary or `ollama run`
must never be able to smuggle extra flags or shell metacharacters.
"""
import pytest

from core.validation import (
    sanitize_filename,
    validate_model_name,
    validate_output_dir,
    validate_target,
    validate_url,
)


class TestValidateTargetAccepts:
    @pytest.mark.parametrize(
        "target",
        [
            "example.com",
            "sub.example.com",
            "127.0.0.1",
            "192.168.1.10",
            "::1",
            "2001:db8::1",
            "10.0.0.0/24",
            "192.168.0.0/16",
            "https://example.com",
            "http://192.168.1.1:8080/path",
        ],
    )
    def test_accepts_legitimate_targets(self, target):
        assert validate_target(target) == target

    def test_strips_surrounding_whitespace(self):
        assert validate_target("  example.com  ") == "example.com"


class TestValidateTargetRejects:
    @pytest.mark.parametrize(
        "target",
        [
            "",
            "   ",
            "-oN /tmp/out",
            "--script=vuln",
            "-",
            "; rm -rf /",
            "example.com; id",
            "example.com | cat /etc/passwd",
            "example.com && id",
            "exam ple.com",
            "example.com`id`",
            "example.com$(id)",
            "a" * 300,  # overlong (MAX_TARGET_LEN = 255)
            "http://user:pass@example.com",
            "ftp://example.com",
            "gopher://example.com",
            "example.com/foo",  # slash but not a CIDR
            "not a host!",
            # NOTE: "256.256.256.256" is NOT rejected: it is a syntactically
            # valid hostname (all-numeric labels) even though it is not a
            # valid IP. It cannot inject flags; nmap would simply fail to
            # resolve it, so accepting it is safe.
        ],
    )
    def test_rejects_malicious_or_invalid_targets(self, target):
        with pytest.raises(ValueError):
            validate_target(target)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            validate_target(None)


class TestValidateUrl:
    def test_accepts_private_hosts_on_purpose(self):
        # PENTIA is an internal pentest tool: private/loopback targets are
        # legitimate by design (see core/validation.py).
        assert validate_url("http://192.168.1.1/admin") == "http://192.168.1.1/admin"
        assert validate_url("https://127.0.0.1:8443/") == "https://127.0.0.1:8443/"

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "file:///etc/passwd",
            "http://user:pass@example.com",
            "https://user@example.com",
            "http://",
            "example.com",
            "http://exa mple.com",
        ],
    )
    def test_rejects_bad_urls(self, url):
        with pytest.raises(ValueError):
            validate_url(url)


class TestValidateModelName:
    @pytest.mark.parametrize("model", ["qwen2.5-coder", "llama3.1:8b", "pentia-v2"])
    def test_accepts_real_model_names(self, model):
        assert validate_model_name(model) == model

    @pytest.mark.parametrize(
        "model", ["--insecure", "-x", "--verbose", "a b", "a;b", "a|b", "", "a" * 70]
    )
    def test_rejects_flag_like_or_weird_names(self, model):
        with pytest.raises(ValueError):
            validate_model_name(model)


class TestValidateOutputDir:
    def test_rejects_dotdot_escape(self, tmp_path):
        with pytest.raises(ValueError):
            validate_output_dir("../escape", base=tmp_path)

    def test_rejects_absolute_path_outside_base(self, tmp_path):
        with pytest.raises(ValueError):
            validate_output_dir("/etc", base=tmp_path)

    def test_accepts_inside_base(self, tmp_path):
        out = validate_output_dir(str(tmp_path / "reports"), base=tmp_path)
        assert str(out).startswith(str(tmp_path.resolve()))


class TestSanitizeFilename:
    def test_traversal_is_neutralised(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32") == "system32"
        assert "/" not in sanitize_filename("a/b/c.json")

    def test_rejects_empty_or_dotdot(self):
        with pytest.raises(ValueError):
            sanitize_filename("..")
        with pytest.raises(ValueError):
            sanitize_filename("")
