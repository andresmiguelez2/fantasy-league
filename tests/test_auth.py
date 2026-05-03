import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from core.security import (
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
    @patch("core.security.pg_connect")
    def test_authenticate_user_success(self, mock_pg_connect):
        """Test successful user authentication"""
        from core.security import authenticate_user
        
        # Create a mock password hash
        password = "test_password"
        password_hash = get_password_hash(password)
        
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "testuser", password_hash, 10)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Authenticate user
        user = authenticate_user("testuser", password)
        
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], 1)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["player_id"], 10)
    
    @patch("core.security.pg_connect")
    def test_authenticate_user_wrong_password(self, mock_pg_connect):
        """Test authentication with wrong password"""
        from core.security import authenticate_user
        
        password_hash = get_password_hash("correct_password")
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "testuser", password_hash, 10)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Try to authenticate with wrong password
        user = authenticate_user("testuser", "wrong_password")
        
        self.assertIsNone(user)
    
    @patch("core.security.pg_connect")
    def test_authenticate_user_not_found(self, mock_pg_connect):
        """Test authentication when user doesn't exist"""
        from core.security import authenticate_user
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_pg_connect.return_value = mock_conn
        
        # Try to authenticate non-existent user
        user = authenticate_user("nonexistent", "password")
        
        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
