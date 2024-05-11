import requests

BASE_URL = 'http://localhost:5080'

def test_session_crud():
    # Create a session
    create_response = requests.post(f'{BASE_URL}/sessions', json={'name': 'Test Session'})
    create_response_data = create_response.json()
    print(f"response data type is , {type(create_response_data)}, and is {create_response_data}")
    assert create_response.status_code == 200
    session_id = create_response_data[0]['id']
    print(f"Created session with ID: {session_id}")

    # Get the created session
    get_response = requests.get(f'{BASE_URL}/sessions/{session_id}')
    print(f"response data type is , {type(get_response)}, and is {get_response}")
    assert get_response.status_code == 200
    session_data = get_response.json()
    print("Retrieved session:", session_data)


    # Update the session
    update_response = requests.patch(f'{BASE_URL}/sessions/{session_id}', json={'name': 'Updated Session Name'})
    assert update_response.status_code == 200
    print("Updated session:", update_response.json())

    # Delete the session
    delete_response = requests.delete(f'{BASE_URL}/sessions/{session_id}')
    assert delete_response.status_code == 200
    print("Deleted session:", delete_response.json())
    print("Test successful!")

if __name__ == '__main__':
    test_session_crud()
