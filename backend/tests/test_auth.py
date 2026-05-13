import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
)


class TestPasswordHashing(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        """Test that password hashing and verification work correctly"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        self.assertTrue(verify_password(password, hashed))
        
        # Verify incorrect password
        self.assertFalse(verify_password("wrong_password", hashed))
    
    def test_same_password_different_hashes(self):
        """Test that the same password produces different hashes (salt)"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        self.assertNotEqual(hash1, hash2)
        
        # Both should verify correctly
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))


class TestJWTTokens(unittest.TestCase):
    def test_create_and_verify_token(self):
        """Test that JWT token creation and verification work"""
        data = {
            "sub": "123",
            "username": "testuser",
            "player_id": 1
        }
        
        token = create_access_token(data)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        
        # Verify token
        payload = verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "123")
        self.assertEqual(payload["username"], "testuser")
        self.assertEqual(payload["player_id"], 1)
    
    def test_verify_invalid_token(self):
        """Test that invalid tokens return None"""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        self.assertIsNone(payload)


class TestAuthentication(unittest.TestCase):
    @patch("backend.app.core.auth.pg_connect")
    def test_authenticate_user_success(self, mock_pg_connect):
        """Test successful user authentication"""
        from backend.app.core.auth import authenticate_user
        
        # Create a mock password hash
        password = "test_password"
        password_hash = get_password_hash(password)
        
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "testuser", password_hash)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Authenticate user
        user = authenticate_user("testuser", password)
        
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], 1)
        self.assertEqual(user["username"], "testuser")
    
    @patch("backend.app.core.auth.pg_connect")
    def test_authenticate_user_wrong_password(self, mock_pg_connect):
        """Test authentication with wrong password"""
        from backend.app.core.auth import authenticate_user
        
        password_hash = get_password_hash("correct_password")
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "testuser", password_hash, 10)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Try to authenticate with wrong password
        user = authenticate_user("testuser", "wrong_password")
        
        self.assertIsNone(user)
    
    @patch("backend.app.core.auth.pg_connect")
    def test_authenticate_user_not_found(self, mock_pg_connect):
        """Test authentication when user doesn't exist"""
        from backend.app.core.auth import authenticate_user
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Try to authenticate non-existent user
        user = authenticate_user("nonexistent", "password")
        
        self.assertIsNone(user)


class TestRegisterRequestValidation(unittest.TestCase):
    """Test Pydantic validation on RegisterRequest username field."""

    def _make_request(self, username: str, password: str = "validpassword"):
        from pydantic import ValidationError
        from backend.app.api.routers.auth import RegisterRequest
        return RegisterRequest(username=username, password=password)

    def _assert_invalid(self, username: str, fragment: str = ""):
        from pydantic import ValidationError
        from backend.app.api.routers.auth import RegisterRequest
        with self.assertRaises(ValidationError) as ctx:
            RegisterRequest(username=username, password="validpassword")
        if fragment:
            self.assertIn(fragment, str(ctx.exception).lower())

    def test_valid_username(self):
        req = self._make_request("valid_user1")
        self.assertEqual(req.username, "valid_user1")

    def test_username_strips_whitespace(self):
        req = self._make_request("  user1  ")
        self.assertEqual(req.username, "user1")

    def test_username_too_short(self):
        self._assert_invalid("ab", "least")

    def test_username_too_long(self):
        self._assert_invalid("a" * 31, "most")

    def test_username_with_spaces(self):
        self._assert_invalid("bad user", "letters")

    def test_username_with_special_chars(self):
        self._assert_invalid("bad!user", "letters")

    def test_username_minimum_length(self):
        req = self._make_request("abc")
        self.assertEqual(req.username, "abc")

    def test_username_maximum_length(self):
        req = self._make_request("a" * 30)
        self.assertEqual(len(req.username), 30)


class TestRegisterEndpoint(unittest.TestCase):
    """Test the register() handler for duplicate username handling."""

    def _call_register(self, mock_pg_connect, username="testuser", password="validpass123"):
        """Helper to invoke the register endpoint function directly."""
        from backend.app.api.routers.auth import register, RegisterRequest
        req = RegisterRequest(username=username, password=password)
        return register(req)

    @patch("backend.app.api.routers.auth.pg_connect")
    def test_register_duplicate_username_conflict(self, mock_pg_connect):
        """Registering with an already-taken username raises 409."""
        from fastapi import HTTPException
        from backend.app.api.routers.auth import register, RegisterRequest

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # duplicate found

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        req = RegisterRequest(username="existing_user", password="validpass123")
        with self.assertRaises(HTTPException) as ctx:
            register(req)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("already taken", ctx.exception.detail.lower())

    @patch("backend.app.api.routers.auth.pg_connect")
    def test_register_case_insensitive_duplicate(self, mock_pg_connect):
        """Duplicate check uses LOWER() for case-insensitive comparison."""
        from fastapi import HTTPException
        from backend.app.api.routers.auth import register, RegisterRequest

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # duplicate found

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        req = RegisterRequest(username="ExistingUser", password="validpass123")
        with self.assertRaises(HTTPException) as ctx:
            register(req)
        self.assertEqual(ctx.exception.status_code, 409)

        # Verify the SQL query uses LOWER() for the uniqueness check
        executed_sql = mock_cursor.execute.call_args_list[0][0][0]
        self.assertIn("LOWER", executed_sql)

    @patch("backend.app.api.routers.auth.pg_connect")
    def test_register_success(self, mock_pg_connect):
        """Successful registration returns user id and username."""
        from backend.app.api.routers.auth import register, RegisterRequest

        mock_cursor = MagicMock()
        # First fetchone: no duplicate; second fetchone: new user id
        mock_cursor.fetchone.side_effect = [None, (42,)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        req = RegisterRequest(username="new_user", password="validpass123")
        result = register(req)
        self.assertEqual(result["id"], 42)
        self.assertEqual(result["username"], "new_user")

    def test_register_invalid_username_raises_validation_error(self):
        """Username too short raises Pydantic ValidationError before hitting the DB."""
        from pydantic import ValidationError
        from backend.app.api.routers.auth import RegisterRequest

        with self.assertRaises(ValidationError):
            RegisterRequest(username="ab", password="validpass123")

    def test_register_username_with_spaces_raises_validation_error(self):
        """Username with spaces raises Pydantic ValidationError."""
        from pydantic import ValidationError
        from backend.app.api.routers.auth import RegisterRequest

        with self.assertRaises(ValidationError):
            RegisterRequest(username="bad user", password="validpass123")


if __name__ == "__main__":
    unittest.main()
