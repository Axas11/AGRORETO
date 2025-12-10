# tests/test_utils.py
"""
Tests para funciones de utilidad
"""
import pytest
from app.utils import verify_password, get_password_hash


def test_password_hashing():
    """Test: Hash de contraseña se genera correctamente"""
    password = "securepassword123"
    hashed = get_password_hash(password)
    
    # El hash debe ser diferente a la contraseña original
    assert hashed != password
    # El hash debe tener longitud > 0
    assert len(hashed) > 0
    # El hash debe empezar con $2b$ (bcrypt)
    assert hashed.startswith("$2b$")


def test_password_verification():
    """Test: Verificación de contraseña funciona correctamente"""
    password = "mypassword123"
    hashed = get_password_hash(password)
    
    # La contraseña correcta debe verificarse
    assert verify_password(password, hashed) is True
    
    # Una contraseña incorrecta no debe verificarse
    assert verify_password("wrongpassword", hashed) is False


def test_different_passwords_different_hashes():
    """Test: Contraseñas diferentes generan hashes diferentes"""
    password1 = "password1"
    password2 = "password2"
    
    hash1 = get_password_hash(password1)
    hash2 = get_password_hash(password2)
    
    assert hash1 != hash2


def test_same_password_different_hashes():
    """Test: La misma contraseña genera hashes diferentes (por salt)"""
    password = "samepassword"
    
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Los hashes son diferentes debido al salt aleatorio
    assert hash1 != hash2
    
    # Pero ambos deben verificar correctamente
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_empty_password():
    """Test: Manejo de contraseña vacía"""
    password = ""
    hashed = get_password_hash(password)
    
    # Debe poder hashear incluso contraseña vacía
    assert len(hashed) > 0
    assert verify_password(password, hashed) is True
