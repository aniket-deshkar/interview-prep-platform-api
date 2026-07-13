from cryptography.fernet import Fernet

from interview_prep.core.security import TokenCipher, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    encoded = hash_password("correct horse battery staple")
    assert encoded != "correct horse battery staple"
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_provider_token_encryption_round_trip() -> None:
    cipher = TokenCipher(Fernet.generate_key().decode())
    encrypted = cipher.encrypt("provider-refresh-token")
    assert encrypted != "provider-refresh-token"
    assert cipher.decrypt(encrypted) == "provider-refresh-token"
