"""Fixture rút gọn theo cấu trúc CISA KEV/NVD; không gọi mạng."""

from datetime import UTC, datetime

import pytest

from portal_api.cves import CveQuery, CveReadService, CvesUnavailable
from portal_api.feeds.import_cves import KEV_URL, NVD_URL, ImportedCveReadPort, import_snapshot
from portal_api.technologies import TechnologyStore

NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)
KEV = {
    "dateReleased": "2026-11-25T10:00:00Z",
    "count": 1,
    "vulnerabilities": [
        {
            "cveID": "CVE-2026-1000",
            "vendorProject": "Fortinet",
            "product": "FortiOS",
            "vulnerabilityName": "Fixture vulnerability",
            "dateAdded": "2026-11-25",
            "dueDate": "2026-12-01",
        }
    ],
}


def nvd_record(cve_id):
    return {
        "cve": {
            "id": cve_id,
            "published": "2026-11-24T10:00:00.000",
            "descriptions": [{"lang": "en", "value": "Fixture NVD description"}],
            "metrics": {"cvssMetricV31": [{"cvssData": {"version": "3.1", "baseScore": 8.8}}]},
            "configurations": [
                {
                    "nodes": [
                        {
                            "cpeMatch": [
                                {
                                    "vulnerable": True,
                                    "criteria": "cpe:2.3:o:fortinet:fortios:*:*:*:*:*:*:*:*",
                                },
                                {
                                    "vulnerable": False,
                                    "criteria": "cpe:2.3:o:other:unrelated:*:*:*:*:*:*:*:*",
                                },
                            ]
                        }
                    ]
                }
            ],
        }
    }


def fetch(url, params=None):
    if url == KEV_URL:
        return KEV
    assert url == NVD_URL
    offset = params["startIndex"]
    return {
        "startIndex": offset,
        "totalResults": 2,
        "resultsPerPage": 1,
        "vulnerabilities": [nvd_record(f"CVE-2026-{1000 + offset}")],
    }


def test_import_paginates_deduplicates_and_matches(tmp_path):
    path = tmp_path / "cves.json"
    import_snapshot(path, 7, fetch, NOW)
    first = path.read_bytes()
    import_snapshot(path, 7, fetch, NOW)
    assert path.read_bytes() == first
    dataset = ImportedCveReadPort(path).list_candidates()
    assert len(dataset.candidates) == 2
    row = dataset.candidates[0]
    assert row["provenance"]["kev_date_added"] == "2026-11-25"
    assert len(row["provenance"]["sources"]) == 2
    store = TechnologyStore(tmp_path / "assets.sqlite")
    store.initialize()
    store.create("Fortinet", "FortiOS", "7.4", "fixture", "test")
    response = CveReadService(ImportedCveReadPort(path), store).read(
        CveQuery(None, None, None, 25, None), "detail"
    )
    assert response["source"]["kind"] == "imported"
    assert response["summary"] == {"matched_cves": 2, "kev_cves": 1}
    assert response["items"][0]["cve_id"] == "CVE-2026-1000"
    assert response["items"][0]["cvss_base_score"] == 8.8


def test_incomplete_feed_does_not_replace_snapshot(tmp_path):
    path = tmp_path / "cves.json"
    import_snapshot(path, 7, fetch, NOW)
    original = path.read_bytes()

    def broken(url, params=None):
        if url == NVD_URL:
            raise RuntimeError("offline")
        return fetch(url, params)

    with pytest.raises(RuntimeError):
        import_snapshot(path, 7, broken, NOW)
    assert path.read_bytes() == original
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(CvesUnavailable):
        ImportedCveReadPort(path).list_candidates()


def test_fetcher_rejects_redirect_and_unknown_endpoint(monkeypatch):
    import httpx

    from portal_api.feeds.import_cves import FeedError, Fetcher

    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://example.invalid/other"})

    monkeypatch.setenv("NVD_API_KEY", "test-only-key")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        fetcher = Fetcher(client)
        with pytest.raises(FeedError, match="HTTP 302"):
            fetcher(KEV_URL)
        with pytest.raises(FeedError, match="Endpoint"):
            fetcher("https://example.invalid/other")
        with pytest.raises(FeedError, match="HTTP 302"):
            fetcher(NVD_URL)
    assert len(requests) == 2
    assert "apiKey" not in requests[0].headers
    assert requests[1].headers["apiKey"] == "test-only-key"
    assert "test-only-key" not in str(requests[1].url)


def test_fetcher_size_limit(monkeypatch):
    import httpx

    from portal_api.feeds import import_cves

    monkeypatch.setattr(import_cves, "MAX_PAGE_BYTES", 10)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x" * 11))
    ) as client:
        with pytest.raises(import_cves.FeedError):
            import_cves.Fetcher(client)(KEV_URL)


def test_config_explicit_provider(tmp_path):
    from portal_api.settings import Settings, SettingsError

    env = {
        "W05_DB_PATH": str(tmp_path / "db.sqlite"),
        "CF_ACCESS_ISSUER": "https://access.synthetic.test",
        "CF_ACCESS_AUD": "b24",
        "CF_ACCESS_JWKS_URL": "https://access.synthetic.test/certs",
        "PORTAL_ORIGIN": "https://portal.synthetic.test",
        "W05_ROLES_JSON": "{}",
    }
    assert Settings.from_env(env).cve_feed_path is None
    with pytest.raises(SettingsError):
        Settings.from_env({**env, "W03_CVE_PROVIDER": "imported"})
    with pytest.raises(SettingsError):
        Settings.from_env({**env, "W03_CVE_PROVIDER": "unknown"})
    path = tmp_path / "cves.json"
    assert (
        Settings.from_env(
            {
                **env,
                "W03_CVE_PROVIDER": "imported",
                "W03_CVE_FEED_PATH": str(path),
            }
        ).cve_feed_path
        == path
    )


def test_inconsistent_nvd_paging_fails_closed(tmp_path):
    from portal_api.feeds.import_cves import FeedError

    def inconsistent(url, params=None):
        result = fetch(url, params)
        if url == NVD_URL and params["startIndex"]:
            return {**result, "totalResults": 3}
        return result

    path = tmp_path / "cves.json"
    with pytest.raises(FeedError):
        import_snapshot(path, 7, inconsistent, NOW)
    assert not path.exists()


def test_kev_unavailable_still_imports_nvd(tmp_path):
    from portal_api.feeds.import_cves import FeedError

    def missing(url, params=None):
        if url != NVD_URL:
            raise FeedError("HTTP 403")
        return fetch(url, params)

    path = tmp_path / "cves.json"
    result = import_snapshot(path, 7, missing, NOW)
    assert result["kev"] == 0 and result["nvd"] == 2
    assert result["kev_catalog"] == "unavailable"
    dataset = ImportedCveReadPort(path).list_candidates()
    assert dataset.kev_snapshot_complete is False
    assert all(x["kev"]["known_exploited"] is None for x in dataset.candidates)
    store = TechnologyStore(tmp_path / "assets.sqlite")
    store.initialize()
    store.create("Fortinet", "FortiOS", "7.4", "fixture", "test")
    service = CveReadService(ImportedCveReadPort(path), store)
    response = service.read(CveQuery(None, None, None, 25, None), "detail")
    assert response["source"]["kev_catalog"] == "unavailable"
    assert response["summary"]["matched_cves"] == 2
    assert response["items"][0]["kev"] is None
    assert response["items"][0]["kev_as_of"] is None
    for kev in (True, False):
        assert service.read(CveQuery(kev, None, None, 25, None), "detail")["items"] == []


def test_official_mirror_provenance(tmp_path):
    from portal_api.feeds.import_cves import KEV_MIRROR_URL, FeedError

    calls = []

    def fallback(url, params=None):
        calls.append(url)
        if url == KEV_URL:
            raise FeedError("HTTP 403")
        if url == KEV_MIRROR_URL:
            return KEV
        return fetch(url, params)

    path = tmp_path / "cves.json"
    result = import_snapshot(path, 7, fallback, NOW)
    assert result["kev_catalog"] == "github"
    assert calls[:2] == [KEV_URL, KEV_MIRROR_URL]
    dataset = ImportedCveReadPort(path).list_candidates()
    assert dataset.kev_snapshot_complete is True
    assert dataset.candidates[0]["provenance"]["sources"][0]["url"] == KEV_MIRROR_URL
    assert dataset.candidates[0]["kev"]["known_exploited"] is True
