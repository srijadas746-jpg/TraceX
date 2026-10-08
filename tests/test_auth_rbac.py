import pytest

def test_t06_unauthorized_role_access(test_env):
    """
    T06: Unauthorized role -> 403 / denied access
    """
    client = test_env["client"]

    # 1. Unauthenticated request to protected route
    res = client.get("/cases", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]

    # 2. Login as INVESTIGATOR
    login_res = client.post("/auth/login", data={
        "username": "investigator",
        "password": "Investigator@123"
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # 3. Investigator trying to access ADMIN-only user management route -> 403 Forbidden
    admin_page_res = client.get("/admin/users")
    assert admin_page_res.status_code == 403

    # 4. Investigator trying to execute case deletion (Admin only) -> 403
    del_res = client.post("/cases/1/delete")
    assert del_res.status_code == 403

    # 5. Sign out and login as ADMIN
    client.get("/auth/logout")
    admin_login = client.post("/auth/login", data={
        "username": "admin",
        "password": "AdminPassword@123"
    }, follow_redirects=True)
    assert admin_login.status_code == 200

    # 6. Admin accessing /admin/users -> 200 OK
    admin_allowed = client.get("/admin/users")
    assert admin_allowed.status_code == 200
    assert b"User &amp; Role Management" in admin_allowed.data or b"User & Role Management" in admin_allowed.data
