import bcrypt


BCRYPT_ROUNDS = 12

# primeste parola si o transforma in hash
def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )

    return hashed_password.decode("utf-8")

# verificare daca parola introdusa de utilizator corespunde cu hash ul stocat in baza de date
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )