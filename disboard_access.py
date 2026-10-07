#!/usr/bin/env python3
"""Local credential registry and revocable web sessions for Disboard."""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path


DATA_DIR = Path(os.environ.get("DISBOARD_DATA_DIR", ".disboard-local")).expanduser()
DATABASE_PATH = DATA_DIR / "access.sqlite3"
SESSION_SECONDS = 8 * 60 * 60
SCRYPT_N = 2**14


class AccessRegistry:
    def __init__(self, database_path=DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.database_path.parent.chmod(0o700)
        except OSError:
            pass
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY COLLATE NOCASE,
                    salt BLOB NOT NULL,
                    key_hash BLOB NOT NULL,
                    created_at INTEGER NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash BLOB PRIMARY KEY,
                    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
                """
            )
        try:
            self.database_path.chmod(0o600)
        except OSError:
            pass

    @staticmethod
    def _hash_key(access_key, salt):
        return hashlib.scrypt(
            access_key.encode("utf-8"), salt=salt, n=SCRYPT_N, r=8, p=1, dklen=32
        )

    def add_user(self, username):
        username = username.strip()
        if not username or len(username) > 80:
            raise ValueError("El usuario debe tener entre 1 y 80 caracteres.")
        access_key = secrets.token_urlsafe(32)
        salt = secrets.token_bytes(16)
        key_hash = self._hash_key(access_key, salt)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO users(username, salt, key_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, salt, key_hash, int(time.time())),
            )
        return access_key

    def list_users(self):
        with self._connect() as connection:
            return connection.execute(
                "SELECT username, created_at, active FROM users ORDER BY username"
            ).fetchall()

    def revoke_user(self, username):
        with self._connect() as connection:
            result = connection.execute(
                "UPDATE users SET active = 0 WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            )
            connection.execute(
                "DELETE FROM sessions WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            )
            return result.rowcount == 1

    def authenticate(self, username, access_key):
        with self._connect() as connection:
            user = connection.execute(
                "SELECT username, salt, key_hash FROM users "
                "WHERE username = ? COLLATE NOCASE AND active = 1",
                (username.strip(),),
            ).fetchone()
        if user is None:
            self._hash_key(access_key, b"disboard-unknown-user")
            return None
        candidate = self._hash_key(access_key, user["salt"])
        return user["username"] if hmac.compare_digest(candidate, user["key_hash"]) else None

    def create_session(self, username):
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).digest()
        expires_at = int(time.time()) + SESSION_SECONDS
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))
            connection.execute(
                "INSERT INTO sessions(token_hash, username, expires_at) "
                "SELECT ?, username, ? FROM users WHERE username = ? COLLATE NOCASE AND active = 1",
                (token_hash, expires_at, username),
            )
        return token

    def session_user(self, token):
        if not token:
            return None
        token_hash = hashlib.sha256(token.encode("utf-8")).digest()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT users.username FROM sessions JOIN users USING(username) "
                "WHERE sessions.token_hash = ? AND sessions.expires_at > ? AND users.active = 1",
                (token_hash, int(time.time())),
            ).fetchone()
        return row["username"] if row else None

    def revoke_session(self, token):
        if not token:
            return
        token_hash = hashlib.sha256(token.encode("utf-8")).digest()
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))