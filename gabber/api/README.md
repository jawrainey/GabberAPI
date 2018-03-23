# Gabber API

All requests are returned in the following format where errors contains unique _keys_ for lookup:

```json
{
  "data": [],
  "meta": {
    "errors": [ "AUTH_USER_UNKNOWN", "PROJECTS_TITLE_EXISTS" ],
    "success": true
  }
}
```

## Authentication

<details>
<summary>users.register</summary>
<br>

`POST: /api/auth/register/`
  
> Create a new user and emails a user a unique token to verify their account

**Arguments**

- `fullname`: the full name of a user, or what they consider their display name to be. This is **not** validated as
fullname varies across countries, where some consider middle name, etc.
- `email`: must be a valid email address and is used to uniquely identify a user.
- `password`: must be at least 12 characters.

**Returns:**

- Within the custom response: `data` is `null` and `success` is `True`

**Actions:**

- Emails the user a unique token to verify their account.

**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_FULLNAME_REQUIRED`: A full name is required to register. This is for others to identify you.
- `AUTH_EMAIL_DOES_NOT_EXIST`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long
</details>

<details>
<summary>users.verify</summary>
<br>

`POST: /api/auth/verify/<token>/`
  
> A magic URL is sent to the user after registering. Once clicked, the user is verified and the associated
user object and tokens are returned.

**Arguments**

- N/A

**Returns:**

```json
{
        "tokens": {
            "access": "",
            "refresh": ""
        },
        "user": {
            "created_on": "14-Mar-2018",
            "email": "hello@me.com",
            "fullname": "Jay Rainey",
            "id": 102,
            "registered": false,
            "updated_on": "14-Mar-2018"
        }
    }
```

**Actions:**

- Emails the user a welcome message.

**Errors**

- `TOKEN_EXPIRED`: The token provided has expired; default length is one week.
- `TOKEN_404`: The token provided is invalid.
- `ALREADY_VERIFIED`: The magic URL has already been used to verify the account.

</details>


<details>
<summary>users.login</summary>
<br>

`POST: /api/auth/login/`

> authenticates a known user and returns a JWT

**Arguments**

- `email`: Must be a valid email address and is used to uniquely identify a user.
- `password`: Must be at least 12 characters.

**Returns:**

- Same as registration

**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_EMAIL_EXISTS`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_INCORRECT_PASSWORD`: An incorrect password was provided for this email address.
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long
</details>

<details>
<summary>users.me</summary>
<br>

`POST: /api/auth/me/`

> Provides access to the user object.

**Arguments**

N/A, but a JWT must be provided.

**Returns:**

- The user object if a JWT is provided, otherwise data is empty.

</details>

<details>
<summary>users.forgot</summary>
<br>
 
`POST: /api/auth/forgot/`

> Emails a user with a time serialised URL that can be used to reset their password

**Arguments**

- `email`: the email address of the user to reset the password for

**Returns**

- N/A

**Actions**

- Emails a _unique_ [timed serializer URL](http://pythonhosted.org/itsdangerous/) (i.e. token) to reset password

**Errors**:

- `GENERAL_INVALID_JSON`: The request you made contains invalid JSON.
- `AUTH_INVALID_EMAIL`: You have not provided a valid email address.
- `AUTH_EMAIL_KEY_REQUIRED`: The attribute `email` is required in your request body.
- `AUTH_EMAIL_IS_EMPTY`: The attribute `email` must not be empty.
- `AUTH_EMAIL_IS_NOT_STRING`: The attribute `email` must be a string.

</details>

<details>
<summary>users.resetPassword</summary>
<br>

`POST: /api/auth/reset/<string:token>/`

> Changes the password of a given email if the token sent is also valid.

**Arguments**

- `password`: the password to change the email address to

**Returns**

- Same as registration

**Actions**

- Emails the user to inform them that their password was reset

**Errors**:

- `GENERAL_INVALID_JSON:` The request made contains invalid JSON
- `AUTH_PASSWORD_KEY_REQUIRED`: The password attribute is required.
- `AUTH_PASSWORD_IS_EMPTY`: The provided password attribute is empty.
- `AUTH_PASSWORD_IS_NOT_STRING`: The password attribute must be a string.
- `TOKEN_EXPIRED`: The token is invalid as it has expired.
- `TOKEN_404:` The token does not exist.
- `TOKEN_USED`: This token was previously used to reset the password.
  
</details>

---

## Projects

<details>
<summary>projects.index</summary>
<br>
  
`GET: /api/projects/`

> Returns a list of available projects for that user; if no JWT provided then public projects are returned.

**Returns**

```json
[
    {
        "created_on": "04-Mar-2018",
        "creator": {
            "fullname": "Jay Rainey",
            "user_id": 13
        },
        "description": "now now",
        "has_consent": false,
        "id": 7,
        "is_active": true,
        "members": [
            {
                "confirmed": true,
                "date_accepted": "13-Mar-2018",
                "date_sent": "13-Mar-2018",
                "deactivated": false,
                "fullname": "jay",
                "role": "user",
                "user_id": 102
            }
        ],
        "privacy": "private",
        "slug": "new",
        "title": "new",
        "topics": [
            {
                "created_on": "04-Mar-2018",
                "id": 10,
                "is_active": 1,
                "project_id": 7,
                "text": "lol",
                "updated_on": "04-Mar-2018"
            }
        ],
        "updated_on": "04-Mar-2018"
    },
    {
        "created_on": "04-Mar-2018",
        "creator": {
            "fullname": "Jay Rainey",
            "user_id": 13
        },
        "description": "new desc",
        "has_consent": false,
        "id": 2,
        "is_active": true,
        "members": [
            {
                "confirmed": true,
                "date_accepted": "12-Mar-2018",
                "date_sent": "12-Mar-2018",
                "deactivated": false,
                "fullname": "jay",
                "role": "admin",
                "user_id": 30
            }
        ],
        "privacy": "public",
        "slug": "ni-oal",
        "title": "ni oal",
        "topics": [
            {
                "created_on": "04-Mar-2018",
                "id": 3,
                "is_active": 1,
                "project_id": 2,
                "text": "one topic lol",
                "updated_on": "04-Mar-2018"
            },
            "..."
        ],
        "updated_on": "04-Mar-2018"
    }
]
```

**Errors**:

- `GENERAL.UNKNOWN_USER:` The user making the request does not exist, i.e. they are JWT user but unknown to our system.

</details>

<details>
<summary>projects.create</summary>
<br>
  
`POST: /api/projects/`

> Creates a new project

**Arguments**

```json
{
  "title": "The title of your neat project",
  "description": "Describe your project ...",
  "privacy": "public | private",
  "topics": ["Topics must strings", "Otherwise madness occurs"]
}
```

**Returns**

The same format as `/projects/`, but for the individual project the user just created

```json
{
    "created_on": "05-Mar-2018",
    "creator": {
        "user_id": 22,
        "fullname": "jay rainey"
    },
    "description": "new desc",
    "has_consent": false,
    "id": 11,
    "is_public": true,
    "is_active": true,
    "members": [
        {
            "id": 22,
            "name": "jay rainey",
            "role": "admin",
            "user_id": 22
        }
    ],
    "slug": "super-new-title",
    "title": "Super new title",
    "topics": [
        {
            "created_on": "05-Mar-2018",
            "id": 14,
            "is_active": 1,
            "project_id": 11,
            "text": "topics",
            "updated_on": "05-Mar-2018"
        }
    ],
    "updated_on": "05-Mar-2018"
}
```

**Errors**:

- `PROJECTS_TITLE_EXISTS`: A project with that title already exists.
- `PROJECTS_TITLE_REQUIRED`: The value for the title parameter is required.
- `PROJECTS_TITLE_IS_NOT_STRING`: The value for the title parameter must be a string.
- `PROJECTS_DESCRIPTION_REQUIRED`: The value for the description parameter is required.
- `PROJECTS_DESCRIPTION_IS_NOT_STRING`: The value for the description parameter must be a string.
- `PROJECTS_PRIVACY_REQUIRED`: The value for the privacy parameter is required.
- `PROJECTS_PRIVACY_INVALID`: The value for the privacy parameter is invalid, which must be private or public.
- `PROJECTS_PRIVACY_IS_NOT_STRING`: The value for the privacy parameter must be a string.
- `PROJECTS_TOPICS_REQUIRED`: The value for the title parameter is required.
- `PROJECTS_TOPIC_MUST_BE_LIST`: The topics parameter must be of type list.
- `PROJECTS_TOPIC_IS_NOT_STRING`: The value for the privacy parameter must be a string.
- `PROJECTS_TOPIC_IS_EMPTY`: A topic provided is empty.
- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `GENERAL_INVALID_JSON`: The request made contains invalid JSON

</details>

### Project

<details>
<summary>projects.show</summary>
<br>
  
`GET: /api/projects/<int:pid>/`

> Returns a project if it is public. If it is private, data is only returned if the JWT user is a member.

**Returns**

```json
    {
        "created_on": "03-Mar-2018",
        "creator": {
            "user_id": 1,
            "fullname": "Jay Rainey"
        },
        "description": "Describe your project in at most 230 words",
        "has_consent": false,
        "id": 11,
        "is_public": true,
        "is_active": true,
        "members": [
            {
                "fullname": "Jay Rainey",
                "role": "user",
                "user_id": 1
            }
            "..."
        ],
        "topics": [
            {
                "created_on": "03-Mar-2018",
                "id": 1,
                "is_active": 0,
                "project_id": 1,
                "text": "Topics must be less than 280 words",
                "updated_on": "03-Mar-2018"
            }
            "..."
        ],
        "slug": "the-title-of-your-a",
        "title": "The title of your a",
        "updated_on": "05-Mar-2018"
    }
```

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.

</details>

<details>
<summary>projects.update</summary>
<br>
  
`PUT: /api/projects/<int:pid>/`

> Updates attributes of an existing project

**Arguments**

Same `object` as when getting, creating, etc, however, the `topics` field must include the following attributes as
it overrides all existing topics for the project; `text` and `is_active` is required for all topics:

**Create:** if no ID is provided, then a topic is created.
**Update:** the `id`, `text` and `is_active` of the topic. The text is overridden for that topic ID.
**Delete:** The topics list must include `is_active`, which if flagged as `false` will soft-delete a topic.

```json
    {
        "id": 12,
        "title": "你好吗?",
        "description": "你好",
        "creator": 30,
        "privacy": "private",
        "topics": [
            {
                "text": "你好 ANOTHER NEW", "is_active": 1
            },
            {
                "id": 4563, "text": "MODIFIED AGAIN 你好", "is_active": 1
            },
                    {
                "id": 4564, "text": "DELETED 你好", "is_active": 0
            }
        ]
    }
```

**Returns**

- The updated, serialized project as in `GET` containing the updated details.

**Errors**

- `ID_404`: The project ID provided in the request does not match the resource endpoint.
- `UNAUTHORIZED`: You do not have the permission to edit this project.
- `USER_NOT_FOUND`: No user for the creator ID provided in the request exists.
- `TITLE_EXISTS`: There already exists a project with that title; titles must be unique.
- `PROJECTS_PRIVACY_INVALID`: The value for the privacy parameter is invalid, which must be private or public.
- `TOPICS_IS_NOT_DICT`: The value for the topics parameter must be a string.
- `TOPICS_IS_ACTIVE_KEY_404`: An is_active key is missing from your topics array.
- `TOPICS_IS_ACTIVE_MUST_BE_INT`: The value of is_active must be an integer.
- `TOPICS_IS_ACTIVE_MUST_BE_0_OR_1`: The value of is_active must be either 0 (false) or 1 (true).
- `TOPICS_ID_NOT_PROJECT`: The ID of a topic does not exist for this project.
- `TOPICS_TEXT_KEY_404`: A text key is missing from your topics array.
- `TOPICS_TEXT_IS_NOT_STRING`: The value of a text must be a string.

</details>

<details>
<summary>projects.destroy</summary>
<br>

`DELETE: /api/projects/<int:pid>/`

> Soft deletes an existing project. The JWT user must have the creator role of a project to delete it.

**Arguments** N/A
**Returns**

- `meta.success` will be True if successful.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_DELETE_UNAUTHORIZED`: ??

</details>

## Project membership

<details>
<summary>projects.members.invites.create</summary>
<br>
  
`POST: /api/project/<int:id>/membership/invites/`

> Adds a member to a project (or creates a user if not exists) and invites them to be part of a given project. If
the system knows the user and they are registered (i.e. active), then they are emailed to inform them that they were
added to the project. Otherwise, a unique token is emailed to the participant where they can register if they do not
have an account or login with a different account (i.e. because the email they received the invite to is personal).

**Arguments**

```json
    {
      "fullname": "Jay Rainey",
      "email": "membertoinvite@gmail.com"
    }
```

**Actions**

This depends if the user is registered:

1) If the user is registered, they are emailed to inform them that they were added to the project
2) Otherwise, the email contains a unique `token` that will let the user create a new account or
login with an existing account, which is then associated with the membership invite.

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `GENERAL_UNKNOWN_USER`: The user in the JWT request does not exist.
- `PROJECT_INVITE_MEMBER_UNAUTHORIZED`: You are unauthorized to remove a member from a project
- `GENERAL_INVALID_JSON`: Your request contains invalid JSON.
- `MEMBERSHIP_FULLNAME_KEY_REQUIRED`: The fullname of a user to add to the project.
- `MEMBERSHIP_FULLNAME_IS_EMPTY`: The fullname of the user provided was empty.
- `MEMBERSHIP_FULLNAME_IS_NOT_STRING`: The fullname of a user must be a string
- `MEMBERSHIP_EMAIL_KEY_REQUIRED`: An email is required of the user to add from the project.
- `MEMBERSHIP_EMAIL_IS_EMPTY`: The email provided for the user to add is empty.
- `MEMBERSHIP_EMAIL_IS_NOT_STRING`: The email provided for the user to add is not a string.
- `MEMBERSHIP_EMAIL_USER_404`: The user you are trying to add does not exist.
- `PROJECT_MEMBER_EXISTS`: A user with that email is already a member of the project.

</details>

<details>
<summary>projects.members.invites.destroy</summary>
<br>
  
`DELETE: /api/project/<int:id>/membership/invites/<int:member_id>`

> Removes a user and emails them that they have been removed from a project, when and by whom.

**Arguments**

N/A

**Returns**

- The member object for the deleted member.

**Actions**

- Emails the user that they have been removed from a project, when and by whom.

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `GENERAL_UNKNOWN_USER`: The user in the JWT request does not exist.
- `PROJECT_INVITE_MEMBER_UNAUTHORIZED`: You are unauthorized to remove a member from a project
- `USER_NOT_PROJECT_MEMBER`: The user you tried to remove is not a member of this project.
- `UNKNOWN_MEMBERSHIP`: The user you tried to remove is not a project member.
- `USER_ALREADY_DELETED`: The user you tried to remove has already been deleted.
 
</details>


<details>
<summary>projects.invites.show</summary>
<br>

`GET: /api/projects/invites/<token>/`
  
> Provides the API consumer with metadata associated with the token, namely the associated users Full Name and Email.

**Arguments**

- `token`: a valid `TimedSerializer` url token.

**Returns:**

```json
  {
    "project": {
        "created_on": "2018-03-19T10:51:45+00:00",
        "creator": {
            "fullname": "Geoff Testington",
            "user_id": 1
        },
        "description": "All that chat you will ever need to have about your boy Geoff Testington",
        "has_consent": false,
        "id": 1,
        "is_active": true,
        "is_public": true,
        "members": [
            {
                "confirmed": true,
                "date_accepted": "2018-03-19T10:51:45+00:00",
                "date_sent": "2018-03-19T10:51:45+00:00",
                "deactivated": false,
                "id": 1,
                "role": "admin",
                "user_id": 9
            },
            "..."
        ],
        "privacy": "public",
        "slug": "geoff-s-super-sessions",
        "title": "Geoff's Super Sessions",
        "topics": [
            {
                "created_on": "2018-03-19T10:51:45+00:00",
                "id": 1,
                "is_active": 1,
                "project_id": 1,
                "text": "Topper Box",
                "updated_on": "2018-03-19T10:51:45+00:00"
            },
            "..."
        ],
        "updated_on": "2018-03-21T19:18:03+00:00"
    },
    "user": {
        "created_on": "2018-03-22T15:34:41+00:00",
        "email": "hi@robo.me",
        "fullname": "Robster McMuffin",
        "id": 18,
        "participant_of": [],
        "registered": false,
        "updated_on": "2018-03-22T15:34:41+00:00",
        "verified": false
    }
  }
```

**Errors**

- `TOKEN_EXPIRED`: The token provided has expired; default length is one week.
- `TOKEN_404`: The token provided is invalid.

</details>

<details>
<summary>projects.invites.accept</summary>
<br>

`PUT: /api/projects/invites/<token>/`
  
> An unregistered user has been invited to a project; they receive a token (magic url) that they can use to modify
their user record (such as fullname) and to accept the invite to join this project.

**Arguments**

- `fullname`: the full name of a user, or what they consider their display name to be.
- `password`: the password for their account.

**Returns:**

The user object:

```json
{
        "tokens": {
            "access": "",
            "refresh": ""
        },
        "user": {
            "created_on": "14-Mar-2018",
            "email": "hello@me.com",
            "fullname": "Jay Rainey",
            "id": 102,
            "registered": false,
            "updated_on": "14-Mar-2018"
        }
    }
```

**Errors**

- `TOKEN_EXPIRED`: The token provided has expired; default length is one week.
- `TOKEN_404`: The token provided is invalid.
- `GENERAL_INVALID_JSON`: The request is not valid JSON.
- `MEMBERSHIP_CONFIRMED`: You have already previously confirmed your membership to this project.
- `AUTH_FULLNAME_REQUIRED`: A full name is required to register. This is for others to identify you.
- `AUTH_ALREADY_REGISTERED`: the account has already been confirmed and registered

</details>

## User membership

<details>
<summary>projects.members.join</summary>
<br>
  
`POST: /api/projects/<int:pid>/membership/`

> Join (i.e. become a member) of an existing public project

**Returns**

- True if success, otherwise False within the `meta` object.

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `ALREADY_MEMBER`: You have tried to join a project that you are already a member of.

</details>

<details>
<summary>projects.members.leave</summary>
<br>

`DELETE: /api/projects/<int:pid>/membership/`

> Leaves a project that the user is a member of.

**Returns**

- True if success, otherwise False within the `meta` object.

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `USER_NOT_PROJECT_MEMBER`: You are not a member of that project.

</details>

## Sessions

<details>
<summary>projects.sessions.index</summary>
<br>
  
`GET: /api/projects/<int:pid>/sessions/`

> A list of all sessions for a given project

**Returns**

```json
    [
        {
            "created_on": "04-Mar-2018",
            "creator": {
                "name": "Hey",
                "user_id": 7
            },
            "id": "ba08ff46c7b04719ba46614551aa10d4",
            "participants": [
                {
                    "name": "Jay",
                    "role": "interviewer",
                    "user_id": 6
                },
                {
                    "name": "Henry",
                    "role": "interviewee",
                    "user_id": 8
                }
            ],
            "topics": [
                {
                    "end": "10",
                    "id": 12,
                    "start": "0",
                    "text": "The first topic being discussed"
                },
                "..."
            ],
            "user_annotations": []
        },
        "..."
    ]
```

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `SESSION_UNKNOWN`: The session you tried to view does not exist.

</details>

<details>
<summary>projects.sessions.create</summary>
<br>
  
`POST: /api/projects/<int:pid>/sessions/`

### MOBILE SUPPORT: LEGACY

> Creates a new session for a given project. **Note:** this is currently only used  on the mobile device,
and is a `application/x-www-form-urlencoded` as it expects a `file` and `metadata` from a form.

**Arguments**

- `recording`: An audio recording from the Gabber session
- `creatorEmail`: The email address of the creator of the project; if not provided it is inferred from JWT.
- `participants`: A dictionary of participants that were involved in the session [serialized here](https://github.com/jawrainey/GabberServer/blob/master/gabber/api/schemas/create_session.py#L39-L54),
which should be of the format: `{Name: Jay, Email: blah@jay.me, Role: 0 or 1}`. These should be uppercase and `Role` is a boolean
that represents if the participant was the creator of the interview.
- `prompts`: A dictionary of topics annotated during the discussion [serialized here](https://github.com/jawrainey/GabberServer/blob/master/gabber/api/schemas/create_session.py#L15-L36),
which should be of the format: `{Start: 0, End: 10, PromptID: 21}`.

**Note:**

- The keys from the `prompts` and `particiapnts` are uppercase.
- The errors and response returned from this request differ from other endpoints as they use an old return response.

</details>

### Session

<details>
<summary>projects.session.show</summary>
<br>
  
`GET: /api/projects/<int:pid>/sessions/<string:sid>/`

> An individual Gabber recorded session for a project

**Returns**

```json
    "created_on": "03-Mar-2018",
    "creator": {
        "name": "Jay",
        "user_id": 6
    },
    "id": "1cee9eca335b45bf82a6886e424c9e86",
    "participants": [
        {
            "name": "Jay",
            "role": "interviewer",
            "user_id": 6
        },
        "..."
    ],
    "topics": [
        {
            "end": "8",
            "id": 1,
            "start": "0",
            "text": "Topics must be less than 280 words"
        },
        "..."
    ],
    "user_annotations": [
        {
            "codes": [],
            "comments": [],
            "created_on": "04-Mar-2018",
            "end_interval": 9,
            "id": 1,
            "justification": "first annotation",
            "session_id": "1cee9eca335b45bf82a6886e424c9e86",
            "start_interval": 0,
            "updated_on": "04-Mar-2018",
            "user_id": 1
        },
        "..."
    ]
```

**Errors**

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database.
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `SESSION_UNKNOWN`: The session you tried to view does not exist.

</details>

#### Consent

<details>
<summary>session.consent.show</summary>
<br>
  
`GET: /api/consent/<token>`

> Using a magic URL, a user involved in a session can provide their consent for what they would like to happen
to their audio recording

**Returns**

The `project`, `session`, and `user` associated with the Gabber session that is being consented.


```json
{
    "data": {
        "project": {
            "created_on": "2018-03-19T10:51:45+00:00",
            "creator": {
                "fullname": "Geoff Testington",
                "user_id": 1
            },
            "description": "All that chat you will ever need to have about your boy Geoff Testington",
            "has_consent": false,
            "id": 1,
            "is_active": true,
            "is_public": true,
            "members": [
                {
                    "confirmed": true,
                    "date_accepted": "2018-03-19T10:51:45+00:00",
                    "date_sent": "2018-03-19T10:51:45+00:00",
                    "deactivated": false,
                    "id": 1,
                    "role": "admin",
                    "user_id": 9
                },
                "..."
            ],
            "privacy": "public",
            "slug": "geoff-s-super-sessions",
            "title": "Geoff's Super Sessions",
            "topics": [
                {
                    "created_on": "2018-03-19T10:51:45+00:00",
                    "id": 1,
                    "is_active": 1,
                    "project_id": 1,
                    "text": "Topper Box",
                    "updated_on": "2018-03-19T10:51:45+00:00"
                },
                "..."
            ],
            "updated_on": "2018-03-21T19:18:03+00:00"
        },
        "session": {
            "audio_url": "https://gabber-ncl.s3.amazonaws.com/1/61539890a92f46f78dd41d2f65bcd89b?AWSAccessKeyId=AKIAIWPXLUJXTAOEZ7SA&Expires=1521751447&Signature=wPYelHcTrqeaf1I9WAF0HJuVUW0%3D",
            "created_on": "2018-03-22T18:42:33+00:00",
            "id": "61539890a92f46f78dd41d2f65bcd89b",
            "num_user_annotations": 0,
            "participants": [
                {
                    "role": "interviewer",
                    "user_id": "26"
                },
                {
                    "role": "interviewee",
                    "user_id": "28"
                }
            ],
            "project_id": 1,
            "topics": [
                {
                    "end_interval": 21,
                    "id": 59,
                    "start_interval": 0,
                    "text": "Topper Box",
                    "topic": 1,
                    "topic_id": 1
                }
            ]
        },
        "user": {
            "created_on": "2018-03-22T18:42:33+00:00",
            "id": 28,
            "participant_of": [
                43
            ],
            "registered": false,
            "updated_on": "2018-03-22T18:42:33+00:00",
            "verified": false
        }
    },
    "meta": {
        "messages": [],
        "success": true
    }
}
```

**Errors**

- `TOKEN_EXPIRED`: The token provided has expired; default length is one week.
- `TOKEN_404`: The token provided is invalid.
- `GENERAL_INVALID_JSON`: The request is not valid JSON.

</details>


<details>
<summary>session.consent.update</summary>
<br>
  
`PUT: /api/consent/<token>`

> Updates the consent for a specific session

**Arguments**

- `type`: must be `none`, `private` or `public`.

**Returns**

- `null` data object, with `success` set as `true`.

**Errors**

- `TOKEN_EXPIRED`: The token provided has expired; default length is one week.
- `TOKEN_404`: The token provided is invalid.
- `GENERAL_INVALID_JSON`: The request is not valid JSON.
- `CONSENT_TYPE_KEY_REQUIRED`: The type attribute is required.
- `CONSENT_TYPE_IS_EMPTY`: The type attribute is empty.
- `CONSENT_TYPE_IS_NOT_STRING`: The type attribute must be a string.
- `CONSENT_INVALID_TYPE_VALUE`: The value provided for type is not none, private or public.
        
</details>


## Annotations

<details>
<summary>projects.sessions.annotations.index</summary>
<br>
  
`GET: /api/projects/<int:pid>/sessions/<string:sid>/annotations/`

> A list of user annotations on a recording session

**Returns**

```json
    [
      {
            "comments": [
                {
                    "annotation_id": 1,
                    "content": "beans",
                    "created_on": "03-Mar-2018",
                    "creator": {
                        "fullname": "jay",
                        "user_id": 30
                    },
                    "id": 1,
                    "parent_id": 1,
                    "replies": [
                        1,
                        2,
                        8,
                        9,
                        10,
                        11
                    ],
                    "session_id": "1cee9eca335b45bf82a6886e424c9e86",
                    "updated_on": "09-Mar-2018"
                },
                {
                    "annotation_id": 1,
                    "content": "Responding to FC",
                    "created_on": "03-Mar-2018",
                    "creator": {
                        "fullname": "Jay Rainey",
                        "user_id": 1
                    },
                    "id": 2,
                    "parent_id": 1,
                    "replies": [
                        3
                    ],
                    "session_id": "1cee9eca335b45bf82a6886e424c9e86",
                    "updated_on": "03-Mar-2018"
                },
                ...
            ],
            "content": "Hello world modified text",
            "created_on": "04-Mar-2018",
            "creator": {
                "fullname": "Jay Rainey",
                "user_id": 1
            },
            "end_interval": 10,
            "id": 1,
            "is_active": true,
            "labels": [
                {
                    "id": 1,
                    "text": "lol"
                },
                {
                    "id": 2,
                    "text": "Smash"
                }
                ...
            ],
            "session_id": "1cee9eca335b45bf82a6886e424c9e86",
            "start_interval": 3,
            "tags": [
                1,
                2,
                3
            ],
            "updated_on": "08-Mar-2018"
      },
      "..."
    ]
```

- `replies` currently returns a list of IDs of other comments on this comment. I will update
this once I get recursive serialization working as comments are self referential.
- `labels` and `tags` present the same information, whereas `tags` only contains the IDs of tags, which
simplifies updating the model.


**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??

</details>

<details>
<summary>projects.sessions.annotations.create</summary>
<br>

`POST: /api/projects/<int:pid>/sessions/<string:sid>/annotations/`

> Creates a new user annotation on a session recording

**Arguments**

```json
    {
        "content": "Now updating",
        "start_interval": 20,
        "end_interval": 20,
        "tags": [1,2]
    }
```

Note: the `tags` argument is currently optional (so can be not sent in the request); if an empty list is sent, then all tags are
removed.

**Returns**

- The created annotation object, e.g.

```json
    {
        "comments": [],
        "content": "Hello world",
        "created_on": "09-Mar-2018",
        "end_interval": 10,
        "id": 11,
        "is_active": true,
        "labels": [
            {
                "id": 1,
                "text": "First tag"
            },
            {
                "id": 3,
                "text": "Third tag"
            }
        ],
        "session_id": "1cee9eca335b45bf82a6886e424c9e86",
        "start_interval": 3,
        "tags": [
            1,
            3
        ],
        "updated_on": "09-Mar-2018",
        "user_id": 30
    }
```

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `GENERAL_INVALID_JSON`: ??
- `ANNOTATIONS_CONTENT_REQUIRED`: ??
- `ANNOTATIONS_CONTENT_IS_NOT_STRING`: ??
- `ANNOTATIONS_CONTENT_IS_EMPTY`: ??
- `ANNOTATIONS_START_INTERVAL_REQUIRED`: ??
- `ANNOTATIONS_START_INTERVAL_IS_NOT_INT`: ??
- `ANNOTATIONS_START_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `ANNOTATIONS_END_INTERVAL_REQUIRED`: ??
- `ANNOTATIONS_END_INTERVAL_IS_NOT_INT`: ??
- `ANNOTATIONS_END_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `ANNOTATIONS_START_BEFORE_END`: ??
- `ANNOTATIONS_TAGS_IS_NOT_LIST`: ??
- `ANNOTATIONS_TAG_IS_NOT_INT`: ??

</details>

<details>
<summary>projects.sessions.annotations.destroy</summary>
<br>
  
`DELETE: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`

> Deletes a users annotation on a session recording. Only users who created the annotation can delete it.

**Returns**

- Custom response where `meta.success` is True if the annotation was deleted, otherwise an error below is provided.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER` ??
- `PROJECT_UNAUTHORIZED`: ??
- `ANNOTATIONS_NOT_FOUND`: ??
- `NOT_ANNOTATION_CREATOR`: ??

</details>

## Comments

<details>
<summary>projects.sessions.annotations.comments.create</summary>
<br>
  
`POST: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/`

> Create a **new** comment on an annotation

**Arguments**

The content of the comment

```json
    {
        "content": "The content of the comment"
    }
```

**Returns**

- The comment as an object; `parent_id` is `null` if it is a comment

```json
    {
        "annotation_id": 1,
        "created_on": "09-Mar-2018",
        "creator": {
            "fullname": "jay",
            "user_id": 30
        },
        "id": 15,
        "parent_id": 10,
        "replies": [],
        "content": "again ... updates",
        "session_id": "1cee9eca335b45bf82a6886e424c9e86",
        "updated_on": "09-Mar-2018"
    }
```

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `COMMENT_404`: ??
- `COMMENT_NOT_IN_SESSION`: ??

</details>


<details>
<summary>projects.sessions.annotations.comments.create.self</summary>
<br>
  
`POST: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`

> Creates a new comment on another comment, e.g. nested comments.

**Returns**

- The new comment resource.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `COMMENT_404`: ??
- `COMMENT_NOT_IN_SESSION`: ??

</details>

<details>
<summary>projects.sessions.annotations.comments.destroy</summary>
<br>
  
`DELETE: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`

> Soft-deletes the entire comment, i.e. via an `delete` feature

**Returns**

- N/A

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `COMMENT_404`: ??
- `COMMENT_NOT_IN_SESSION`: ??
- `NOT_COMMENT_CREATOR`: ??

</details>
