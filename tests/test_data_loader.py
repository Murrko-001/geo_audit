import json
import pytest

import src.data_loader as dl


class DummyResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError("HTTP error")

    def json(self):
        return self._payload


def test_fetch_wp_posts_calls_wp_endpoint(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return DummyResp([{"id": 1}])

    monkeypatch.setattr(dl.requests, "get", fake_get)

    out = dl.fetch_wp_posts("https://example.com", per_page=7)
    assert out == [{"id": 1}]
    assert captured["timeout"] == 30
    assert captured["url"] == "https://example.com/wp-json/wp/v2/posts?per_page=7"


def test_save_and_load_posts_roundtrip(tmp_path):
    path = tmp_path / "articles.json"
    data = [{"id": 1}, {"id": 2}, {"id": 3}]

    dl.save_posts_to_file(data, filename=path)
    loaded = dl.load_posts_from_file(filename=path, per_page=2)

    assert loaded == [{"id": 1}, {"id": 2}]


def test_load_posts_from_file_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError):
        dl.load_posts_from_file(filename=path, per_page=10)


def test_load_posts_wrapper_file(tmp_path):
    path = tmp_path / "articles.json"
    path.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")

    out = dl.load_posts_wrapper(use_wp=False, file_name=path, per_page=1)
    assert out == [{"id": 1}]
