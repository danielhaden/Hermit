"""Preferences, and the fallbacks that keep dialogs pointed somewhere real."""

from pathlib import Path

from hermit.model.settings import Settings


def test_unset_keys_return_the_default(settings):
    assert settings.get("nothing-here", "fallback") == "fallback"


def test_library_folder_round_trips(settings, tmp_path, data_dir):
    settings.set_library_folder(tmp_path)
    settings.close()

    reopened = Settings()  # as a restart would see it
    assert reopened.library_folder() == tmp_path
    reopened.close()


def test_browse_folder_defaults_to_home_when_unset(settings):
    assert settings.library_folder() is None
    assert settings.browse_folder() == Path.home()


def test_browse_folder_uses_the_nominated_folder(settings, tmp_path):
    settings.set_library_folder(tmp_path)
    assert settings.browse_folder() == tmp_path


def test_browse_folder_falls_back_when_the_folder_has_moved(settings, tmp_path):
    """A stale setting must not leave the file dialog on a dead path."""
    gone = tmp_path / "since-deleted"
    gone.mkdir()
    settings.set_library_folder(gone)
    gone.rmdir()
    assert settings.browse_folder() == Path.home()
