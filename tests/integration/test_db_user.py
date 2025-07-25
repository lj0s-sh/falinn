import pytest
from tests.utils import make_user_payload
from src.main import app
from src.users.schemas import UserModel
from src.auth.utils import verify_password
from src.auth.dependencies import validate_token

@pytest.mark.asyncio
async def test_me(client, test_token):
    headers = { 'Authorization': f'Bearer {test_token}'}

    response = await client.get('/users/me', headers=headers)

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_me_invalid_token(client):
    headers = { 'Authorization': f'Bearer fake_token'}

    response = await client.get('/users/me', headers=headers)

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_deleted_user_with_valid_token(client, test_db, test_user, test_token):
    await test_db['users'].delete_one({ '_id': test_user['_id'] })
    
    headers = { 'Authorization': f'Bearer {test_token}'}

    response = await client.get('/users/me', headers=headers)

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_user(client, test_db, test_user, override_authentication):
    data = make_user_payload({'email': 'updatetest@example.com'}, exclude=['password'])

    response = await client.put('/users/', json=data)

    update_user = await test_db['users'].find_one({ '_id': test_user['_id'] })

    assert response.status_code == 200
    assert update_user['name'] == data['name']
    assert update_user['last_name'] == data['last_name']
    assert update_user['email'] == data['email']
    assert update_user['password'] == test_user['password']

@pytest.mark.asyncio
async def test_update_user_with_different_password(client, test_db, test_user, override_authentication):
    data = make_user_payload(override={'password': 'test_password'}, exclude=['name', 'last_name', 'email'])

    response = await client.put('/users/', json=data)

    update_user = await test_db['users'].find_one({ '_id': test_user['_id'] })

    assert response.status_code == 200
    assert update_user['password'] != test_user['password']
    assert verify_password(data['password'], update_user['password']) == True

@pytest.mark.asyncio
async def test_update_user_empty_request(client, test_user, override_authentication):
    data = {}

    response = await client.put('/users/', json=data)

    user = response.json()

    assert response.status_code == 200
    assert user['id'] == str(test_user['_id'])
    assert user['name'] == test_user['name']
    assert user['last_name'] == test_user['last_name']
    assert user['email'] == test_user['email']

@pytest.mark.asyncio
async def test_update_user_not_found(client, test_user, test_db, override_authentication):
    await test_db['users'].delete_one({ '_id': test_user['_id'] })

    data = make_user_payload()

    response = await client.put('/users/', json=data)

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_empty_request_user_not_found(client, test_user, test_db, override_authentication):
    await test_db['users'].delete_one({ '_id': test_user['_id'] })

    data = {}

    response = await client.put('/users/', json=data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(client, test_user, test_db, override_authentication):
    response = await client.delete('/users/')

    user = await test_db['users'].find_one({ '_id': test_user['_id'] })

    assert response.status_code == 204
    assert user == None

@pytest.mark.asyncio
async def test_delete_user_valid_token_deleted_user(client, test_user, test_db, override_authentication):
    await test_db['users'].delete_one({ '_id': test_user['_id'] })
    
    response = await client.delete('/users/')

    assert response.status_code == 404