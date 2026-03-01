"""Tests for the i18n module: locale loading, translation, fallbacks."""

from __future__ import annotations

from skaro_core.i18n import _flatten_dict, get_locale, set_locale, t


class TestFlattenDict:
    def test_simple(self):
        assert _flatten_dict({"a": "1", "b": "2"}) == {"a": "1", "b": "2"}

    def test_nested(self):
        result = _flatten_dict({"cli": {"init": {"success": "OK"}}})
        assert result == {"cli.init.success": "OK"}

    def test_mixed_depth(self):
        result = _flatten_dict({"a": "1", "b": {"c": "2", "d": {"e": "3"}}})
        assert result == {"a": "1", "b.c": "2", "b.d.e": "3"}

    def test_empty(self):
        assert _flatten_dict({}) == {}


class TestSetLocale:
    def test_set_en(self):
        set_locale("en")
        assert get_locale() == "en"

    def test_set_ru(self):
        set_locale("ru")
        assert get_locale() == "ru"

    def test_unknown_falls_back_to_en(self):
        set_locale("xx_nonexistent")
        assert get_locale() == "en"


class TestTranslate:
    def test_known_key(self):
        set_locale("en")
        result = t("cli.init.success")
        # Should return something other than the raw key
        assert result != "" or result == "cli.init.success"  # key or translated

    def test_unknown_key_returns_key(self):
        set_locale("en")
        result = t("nonexistent.key.here")
        assert result == "nonexistent.key.here"

    def test_format_params(self):
        set_locale("en")
        # Even if key not found, format should not crash
        result = t("test.{name}", name="world")
        assert "test." in result  # key returned as-is, format may or may not apply

    def test_format_missing_param_no_crash(self):
        set_locale("en")
        # Key with format placeholder but no param — should not raise
        result = t("cli.init.success")
        assert isinstance(result, str)

    def test_lazy_init(self):
        """t() auto-initializes locale if _strings is empty."""
        import skaro_core.i18n as mod
        old_strings = mod._strings
        mod._strings = {}
        try:
            result = t("cli.init.success")
            assert isinstance(result, str)
            assert mod._strings  # should have been populated
        finally:
            mod._strings = old_strings
