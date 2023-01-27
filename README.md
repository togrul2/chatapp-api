# Real time chat app with Fast-API

This app is a real time chat api where people can chat with their friends.

## Commands
### Run server
    First you might need to set PYTHONPATH to src
    $ uvicorn main:app --reload --host localhost --port 8000

### Alembic
    Create migration
    $ alembic revision --autogenerate -n init

    Apply migrations
    $ alembic upgrade head

    Downgrade by 1 migration
    $ alembic downgrade -1

## Functionality

1. Friendship system, people can befriend with each other.
2. Chatting, friends can chat with each other.
3. Groups, people can participate in groups.
4. Sending media files, people can send media files to each other which are not exceeding 10Mb.

## Endpoints

- User
  - `/api/token` [POST], get auth token
  - `/api/users` [GET, POST], list, search and register a user
  - `/api/refresh` [POST], get refresh token
  - `/api/users/me` [GET, PUT, PATCH, DELETE] get, edit and delete authenticated user
  - `/api/users/me/image` [POST, DELETE] upload and remove profile image of authenticated user
  - `/api/users/{id}` [GET] get users info based on their id
  - `/api/user/{username}` [GET] get users info based on their username
- Friends
  - `/api/friendship/requests` [GET] get pending friendship requests
  - `/api/friendship/requests/users/{target_id}` [GET, POST, PATCH, DELETE] get, send, accept and delete friendship requests.
  - `/api/friendship/friends` [GET] get list of friends
