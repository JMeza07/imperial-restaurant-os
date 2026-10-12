from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "Password123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_contains_expected_claims():
    user_id = "11111111-1111-1111-1111-111111111111"
    role = "ADMIN"

    token, jti = create_access_token(user_id, role)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert payload["jti"] == jti


def test_refresh_token_contains_expected_claims():
    user_id = "22222222-2222-2222-2222-222222222222"
    role = "COCINERO"

    token, jti = create_refresh_token(user_id, role)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti
