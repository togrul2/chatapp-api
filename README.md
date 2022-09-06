# REAL TIME CHAT APP WITH FAST-API

This app is a real time chat api where people can chat with their friends.

## Functionality

1. Friendship system, people can add friend with users.
2. Chatting, friends can chat with each other.
3. Groups, people can participate in groups.
4. Sending media files, people can send media files to each other which are not exceeding 10Mb.

## Endpoints

- `/api/token` [POST], get auth token 
- `/api/register` [POST], register a user
- `/api/refresh` [POST], get refresh token
- `/api/users/me` [GET, PUT, PATCH, DELETE] get, edit and delete authenticated user
- `/api/users/{id}` [GET] get users info based on their id
- `/api/user/{username}` [GET] get users info based on their username