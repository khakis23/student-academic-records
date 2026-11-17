from app.models import Student


def register(client, **overrides):
    data = {
        "student_id": "S100",
        "full_name": "Ada Student",
        "email": "ada@example.com",
        "password": "secure123",
    }
    data.update(overrides)
    return client.post("/register", data=data)


def test_registration_creates_account_and_account_can_log_in(client, app):
    response = register(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with app.app_context():
        student = Student.query.filter_by(student_id="S100").one()
        assert student.full_name == "Ada Student"
        assert student.email == "ada@example.com"
        assert student.check_password("secure123")

    login = client.post(
        "/login",
        data={"email": "ada@example.com", "password": "secure123"},
    )
    assert login.status_code == 302


def test_registration_rejects_missing_fields_without_creating_account(
    client, database
):
    response = register(client, full_name="")

    assert response.status_code == 200
    assert b"All fields are required" in response.data
    with client.application.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_malformed_email(client, app):
    response = register(client, email="not-an-email")

    assert response.status_code == 200
    assert b"Enter a valid email address" in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_short_password(client, app):
    response = register(client, password="short")

    assert response.status_code == 200
    assert b"Password must be at least 8 characters" in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_duplicate_student_id(client, app):
    assert register(client).status_code == 302

    response = register(
        client,
        email="other@example.com",
    )

    assert response.status_code == 200
    assert b"student ID already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_rejects_duplicate_email(client, app):
    assert register(client).status_code == 302

    response = register(
        client,
        student_id="S200",
        email="ADA@example.com",
    )

    assert response.status_code == 200
    assert b"email address already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_stores_hashed_password(client, app):
    register(client, password="plaintext")

    with app.app_context():
        student = Student.query.filter_by(student_id="S100").one()
        assert student.password_hash != "plaintext"
        assert student.check_password("plaintext")
