"""
This module contains tests for the application.

It includes tests for the /cryptocurrencies, /users/me, /users/me/assets, /token, and /register endpoints.
It also includes tests for the correct and incorrect credentials for the /token endpoint.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from jose import jwt
from starlette.testclient import TestClient

from src.config import settings
from src.db import UserOperations
from src.main import app
from src.models import User
from src.secutiry import Authentication


HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_NOT_FOUND = 404
TEST_PASSWORD = 'hashed_password'


@pytest.mark.asyncio
async def test_get_cryptocurrencies():
    """
    Test the /cryptocurrencies endpoint.

    This test checks if the endpoint returns the correct status code and response body.
    """
    mock_get_listings_from_db = Mock()
    mock_get_listings_from_db.return_value = [
        {'name': 'Bitcoin', 'symbol': 'BTC', 'price': 50000, 'sync_timestamp': '2022-01-01T00:00:00Z'},
    ]

    with patch('src.db.DB.get_listings_from_db', new=mock_get_listings_from_db):
        client = TestClient(app)
        response = client.get('/cryptocurrencies')
        assert response.status_code == HTTP_STATUS_OK
        assert response.json() == [
            {'name': 'Bitcoin', 'symbol': 'BTC', 'price': 50000, 'sync_timestamp': '2022-01-01T00:00:00Z'},
        ]


@pytest.mark.asyncio
async def test_get_cryptocurrency():
    """
    Test the /cryptocurrencies/{id} endpoint.

    This test checks if the endpoint returns the correct status code and response body for a valid cryptocurrency ID.
    """
    mock_get_listings_from_db = Mock()
    mock_get_listings_from_db.return_value = [
        {
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'price': 50000,
            'sync_timestamp': '2022-01-01T00:00:00Z',
        },
    ]
    with patch('src.db.DB.get_listings_from_db', new=mock_get_listings_from_db):
        client = TestClient(app)
        response = client.get('/cryptocurrencies/1')
        assert response.status_code == HTTP_STATUS_OK
        assert response.json() == {
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'price': 50000,
            'sync_timestamp': '2022-01-01T00:00:00Z',
        }


@pytest.mark.asyncio
async def test_get_cryptocurrency_not_found():
    """
    Test the /cryptocurrencies/{id} endpoint.

    This test checks if the endpoint returns the correct status code when a cryptocurrency ID is not found.
    """
    mock_get_listings_from_db = Mock()
    mock_get_listings_from_db.return_value = [
        {
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'price': 50000,
            'sync_timestamp': '2022-01-01T00:00:00Z',
        },
    ]
    with patch('src.db.DB.get_listings_from_db', new=mock_get_listings_from_db):
        client = TestClient(app)
        response = client.get(f'/cryptocurrencies/{len(mock_get_listings_from_db.return_value)*2}')
        assert response.status_code == HTTP_STATUS_NOT_FOUND


@pytest.mark.asyncio
async def test_read_users_me():
    """
    Test the /users/me endpoint.

    This test checks if the endpoint returns the correct status code and response body for a valid user.
    """
    mock_get_current_active_user = MagicMock()
    mock_get_current_active_user.return_value = User(username='testuser')

    mock_get_username_by_token = AsyncMock()
    mock_get_username_by_token.return_value = 'testuser'

    mock_get_user_by_username_from_db = MagicMock()
    mock_get_user_by_username_from_db.return_value = User(username='testuser')

    with patch('src.router.get_current_active_user', new=mock_get_current_active_user):
        with patch('src.secutiry.Authentication.get_username_by_token', new=mock_get_username_by_token):
            with patch('src.db.UserOperations.get_user_by_username_from_db', new=mock_get_user_by_username_from_db):
                client = TestClient(app)
                client.headers = {'Authorization': 'Bearer test_token'}
                response = client.get('/users/me')
                assert response.status_code == HTTP_STATUS_OK
                assert response.json() == 'testuser'


@pytest.mark.asyncio
async def test_read_users_assets():
    """
    Test the /users/me/assets endpoint.

    This test checks if the endpoint returns the correct status code and response body for a valid user.
    """
    test_assets = [
        {
            'currency': 'Bitcoin',
            'amount': 1.0,
            'current cost': 50000.0,
            'current_price': 50000.0,
        },
        {
            'currency': 'Ethereum',
            'amount': 2.0,
            'current cost': 4000.0,
            'current_price': 2000.0,
        },
    ]

    test_user = User(username='testuser')

    with patch('src.router.get_current_active_user', return_value=test_user):
        with patch('src.db.UserOperations.get_user_assets_info', return_value=test_assets):
            with patch('sqlalchemy.orm.Session.query', return_value=MagicMock()):
                with patch('sqlalchemy.orm.query.Query.filter_by', return_value=MagicMock()):
                    with patch('sqlalchemy.orm.query.Query.all', return_value=[]):
                        client = TestClient(app)
                        client.headers = {'Authorization': 'Bearer test_token'}
                        response = client.get('/users/me/assets')

    assert response.status_code == HTTP_STATUS_OK
    assert response.json() == test_assets


@pytest.fixture
def client():
    """
    Fixture for creating a test client.

    Returns:
        TestClient: A TestClient instance with the application.
    """
    return TestClient(app)


@pytest.fixture
def test_user():
    """
    Fixture for creating a test user.

    Returns:
        User: A User instance with a username and hashed password.
    """
    return User(username='test', hash_password=TEST_PASSWORD)


@patch.object(UserOperations, 'get_user_by_username_from_db')
@patch('src.secutiry.Authentication.generate_jwt_token')
@patch('src.secutiry.Authentication.verify_password')
def test_login_correct_credentials(
    mock_verify_password,
    mock_generate_jwt_token,
    mock_get_user_by_username_from_db,
    client,
    test_user,
):
    """
    Test the /token endpoint with correct credentials.

    This test checks if the endpoint returns the correct status code and response body when the credentials are correct.

    Args:
        mock_verify_password (MagicMock): Mock for the verify_password function.
        mock_generate_jwt_token (MagicMock): Mock for the generate_jwt_token function.
        mock_get_user_by_username_from_db (MagicMock): Mock for the get_user_by_username_from_db function.
        client (TestClient): A TestClient instance for testing.
        test_user (User): A User instance for testing.
    """
    mock_get_user_by_username_from_db.return_value = test_user
    mock_generate_jwt_token.return_value = 'dummy_token'
    mock_verify_password.return_value = True

    response = client.post('/token', json={'username': 'test', 'password': 'password'})

    assert response.status_code == HTTP_STATUS_OK
    assert response.json() == {'token': 'dummy_token', 'token_type': 'bearer'}


@patch.object(UserOperations, 'get_user_by_username_from_db')
def test_login_incorrect_credentials(
    mock_get_user_by_username_from_db,
    client,
):
    """
    Test the /token endpoint with incorrect credentials.

    This test checks if the endpoint returns the correct status code when the credentials are incorrect.

    Args:
        mock_get_user_by_username_from_db (MagicMock): Mock for the get_user_by_username_from_db function.
        client (TestClient): A TestClient instance for testing.
    """
    mock_get_user_by_username_from_db.return_value = None

    response = client.post('/token', json={'username': 'test', 'password': 'wrong_password'})

    assert response.status_code == HTTP_STATUS_BAD_REQUEST


@patch('src.db.UserOperations.get_user_by_username_from_db')
@patch('src.secutiry.Authentication.get_password_hash')
@patch('src.db.UserOperations.create_user')
def test_register(
    mock_create_user,
    mock_get_password_hash,
    mock_get_user_by_username_from_db,
    client,
):
    """
    Test the /register endpoint.

    This test checks if the endpoint returns the correct status code and response body when a new user is registered.

    Args:
        mock_create_user (MagicMock): Mock for the create_user function.
        mock_get_password_hash (MagicMock): Mock for the get_password_hash function.
        mock_get_user_by_username_from_db (MagicMock): Mock for the get_user_by_username_from_db function.
        client (TestClient): A TestClient instance for testing.
    """
    username = 'testuser'
    password = 'testpassword'
    hashed_password = 'hashedpassword'
    user = User(username=username, hash_password=hashed_password)

    mock_get_user_by_username_from_db.return_value = None
    mock_get_password_hash.return_value = hashed_password
    mock_create_user.return_value = user

    response = client.post('/register', json={'username': username, 'password': password})

    assert response.status_code == HTTP_STATUS_CREATED
    assert response.content == b'User created'


def test_generate_jwt_token():
    """
    Test the generate_jwt_token method of the Authentication class.

    This test checks if the method returns a valid JWT token when given correct parameters.
    It also checks if the method raises a ValueError when the encode_data parameter is not a dictionary.
    """
    auth = Authentication()

    username = 'testuser'
    encode_data = {'data': 'test'}
    expires_timedelta = timedelta(minutes=60)

    token = auth.generate_jwt_token(username, encode_data, expires_timedelta)

    decoded_token = jwt.decode(token, settings.TOKEN_SECRET, algorithms=[settings.ALGORITHM])

    assert decoded_token['sub'] == username
    assert decoded_token['data'] == 'test'

    encode_data = 'not a dictionary'
    with pytest.raises(ValueError):
        auth.generate_jwt_token(username, encode_data, expires_timedelta)

