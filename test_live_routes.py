import pytest

def test_all_routes_render_cleanly(test_env):
    """
    Verifies that all views render with HTTP 200 and no Jinja template or runtime errors.
    """
    client = test_env["client"]

    # 1. Login
    client.post("/auth/login", data={
        "username": "investigator",
        "password": "Investigator@123"
    }, follow_redirects=True)

    # 2. Dashboard
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert b"Digital Forensics Command Center" in res.data

    # 3. Cases list
    res = client.get("/cases")
    assert res.status_code == 200
    assert b"Investigation Cases" in res.data

    # 4. Create new case view
    res = client.get("/cases/new")
    assert res.status_code == 200

    # 5. Create a case
    res = client.post("/cases/new", data={
        "title": "Route Verification Incident",
        "incident_type": "Unauthorized Access",
        "description": "Validating all web endpoints."
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Route Verification Incident" in res.data

    case_id = 1
    # 6. Test all case detail tabs
    for tab in ["overview", "evidence", "custody", "logs", "timeline", "findings", "correlation"]:
        res = client.get(f"/cases/{case_id}?tab={tab}")
        assert res.status_code == 200

    # 7. Timeline fullscreen view
    res = client.get(f"/cases/{case_id}/timeline")
    assert res.status_code == 200

    # 8. Report view
    res = client.get(f"/cases/{case_id}/report")
    assert res.status_code == 200
    assert b"Evidentiary Notice" in res.data

    # 9. Report download markdown
    res = client.get(f"/cases/{case_id}/report/download")
    assert res.status_code == 200
    assert "text/markdown" in res.headers.get("Content-Type", "")

    # 10. Report json
    res = client.get(f"/cases/{case_id}/report/json")
    assert res.status_code == 200
    assert "application/json" in res.headers.get("Content-Type", "")
