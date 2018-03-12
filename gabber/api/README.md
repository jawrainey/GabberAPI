# API Documentation: work in progress

All requests are returned in the following format where errors contains unique _keys_ to simplify frontend access:

```json
{
  "data": [],
  "meta": {
    "errors": [ "AUTH_USER_UNKNOWN", "PROJECTS_TITLE_EXISTS" ],
    "success": true
  }
}
```

**Note:** all `POST/PUT` requests must be in `json` format.

The following are errors that can be returned across resources:

- `GENERAL_INVALID_JSON`: The request made contains invalid JSON
- `GENERAL_UNKNOWN_USER`: The user in the JWT request does not exist.

## Authentication

### Endpoint: users.register

`POST: /api/auth/register/`

> Create a new user and returns a JWT

**Arguments**

- `fullname`: the full name of a user, or what they consider their display name to be. This is **not** validated as
fullname varies across countries, where some consider middle name, etc.
- `email`: must be a valid email address and is used to uniquely identify a user.
- `password`: must be at least 12 characters.

**Returns:**

```json
{
  "access_token": "",
  "refresh_token": ""
}
```

**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_FULLNAME_REQUIRED`: A full name is required to register. This is for others to identify you.
- `AUTH_EMAIL_DOES_NOT_EXIST`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long


---

### Endpoint: users.login

`POST: /api/auth/login/`

> authenticates a known user and returns a JWT

**Arguments**

- `email`: Must be a valid email address and is used to uniquely identify a user.
- `password`: Must be at least 12 characters.

**Returns:**

```json
{
  "access_token": "",
  "refresh_token": ""
}
```

**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_EMAIL_EXISTS`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_INCORRECT_PASSWORD`: An incorrect password was provided for this email address.
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long

---

### Endpoint: users.forgot

`POST: /api/auth/forgot/`

> Emails a user with a time serialised URL that can be used to reset their password

**Arguments**

- `email`: the email address of the user to reset the password for

**Returns**

The magic URL that is generated and sent in an email, which could be used on the client to simplify workflow:

```json
{
  "reset_url": "http://0.0.0.0:5000/api/auth/reset/Imphd3JhaW5leUBnbWFpbC5jb20i.DYWvEQ.A_ave4r-iQeCfnDaOnCblF3MsVo"
}
```

**Actions**

- Emails a _unique_ [timed serializer URL](http://pythonhosted.org/itsdangerous/) (i.e. token) to reset password

**Errors**:

- `GENERAL_INVALID_JSON`: The request you made contains invalid JSON.
- `USER_DOES_NOT_EXIST`: The email provided is not associated with a known user.
- `AUTH_INVALID_EMAIL`: You have not provided a valid email address.
- `AUTH_EMAIL_KEY_REQUIRED`: The attribute `email` is required in your request body.
- `AUTH_EMAIL_IS_EMPTY`: The attribute `email` must not be empty.
- `AUTH_EMAIL_IS_NOT_STRING`: The attribute `email` must be a string.
- `ISSUE_SENDING_EMAIL`: An error occurred when trying to send the email. If this continues, please get in touch.

### Endpoint: users.resetPassword

`GET: /api/auth/reset/<string:token>/`

> Returns the email address associated with that token if a token is valid, which can be
used on the frontend to pre-populate fields, etc. This is _not_ used in the following `POST`.

**Arguments**

- N/A

**Returns**

The email address of the user who is visiting the reset page with the magic URL.

```json
{ "email": "notjawrainey@gmail.com" }
```

**Errors**:

- `TOKEN_EXPIRED`: The token is invalid as it has expired.
- `TOKEN_404:` The token does not exist.
- `TOKEN_USED`: This token was previously used to reset the password.

### Endpoint: users.resetPassword

`POST: /api/auth/reset/<string:token>/`

> Changes the password of a given email if the token sent is also valid.

**Arguments**

- `password`: the password to change the email address to

**Returns**

- The same response as login/register, e.g. the access and refresh tokens.

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

---

## Projects

### Endpoint: projects.index

`GET: /api/projects/`

> A dictionary of personal/public projects for a user. If the user is unauthenticated, then the private list is empty.

**Returns**

```json
{
    "personal": [],
    "public": [
        {
            "created_on": "04-Mar-2018",
            "creator": {
                "user_id": 13,
                "fullname": "Jay Rainey"
            },
            "description": "new desc",
            "has_consent": false,
            "id": 2,
            "is_public": true,
            "is_active": true,
            "members": [
                {
                    "fullname": "Jay Rainey",
                    "role": "admin",
                    "user_id": 13
                },
            ],
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
}
```
**Notes**

1) If a project is public and a user is a member then it appears in the personal list.
4) `has_consent` and `is_public` are the configuration properties of a project


**Errors**:

- `GENERAL.UNKNOWN_USER:` The user making the request does not exist, i.e. they are JWT user but unknown to our system.

---

### Endpoint: projects.create

`POST: /api/projects/`

> Creates a new project

**Arguments**

```json
{
  "title": "The title of your neat project",
  "creator": 10,
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

---

### Project (individual project)

Authorized JWT users can view, edit and delete a given project. Only creators of the project can edit or delete,
and only members of a project can view private projects

### Endpoint: projects.show

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

---

### Endpoint: projects.update

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
- `USER_404`: No user for the creator ID provided in the request exists.
- `TITLE_EXISTS`: There already exists a project with that title; titles must be unique.
- `PROJECTS_PRIVACY_INVALID`: The value for the privacy parameter is invalid, which must be private or public.
- `TOPICS_IS_NOT_DICT`: The value for the topics parameter must be a string.
- `TOPICS_IS_ACTIVE_KEY_404`: An is_active key is missing from your topics array.
- `TOPICS_IS_ACTIVE_MUST_BE_INT`: The value of is_active must be an integer.
- `TOPICS_IS_ACTIVE_MUST_BE_0_OR_1`: The value of is_active must be either 0 (false) or 1 (true).
- `TOPICS_ID_NOT_PROJECT`: The ID of a topic does not exist for this project.
- `TOPICS_TEXT_KEY_404`: A text key is missing from your topics array.
- `TOPICS_TEXT_IS_NOT_STRING`: The value of a text must be a string.

---

### Endpoint: projects.destroy

`DELETE: /api/projects/<int:pid>/`

> Soft deletes an existing project. The JWT user must have the creator role of a project to delete it.

**Arguments** N/A
**Returns**

- `meta.success` will be True if successful.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_DELETE_UNAUTHORIZED`: ??

---

## Project membership

This is for when project members join (public) or leave, rather than an admin adding/removing them.

### Endpoint: projects.members.create

`POST: /api/projects/<int:pid>/membership/``

**Description** join (i.e. become a member) of an existing public project

**Returns** True if success, otherwise False within the `meta` object.

**Errors**

- `PROJECT_UNKNOWN`: ??

---

### Endpoint: projects.members.destroy

`DELETE: /api/projects/<int:pid>/membership/`

**Description** leaves a project that the user is a member of.

**Returns** True if success, otherwise False within the `meta` object.

**Errors**

- `TODO`: ??

---

## Sessions

A list of sessions that have been recorded for a particular project.

### Endpoint: projects.sessions.index

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

---

### Endpoint: projects.session.create

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

---

## Session (individual session)

A specific session from the set of sessions for a project

### Endpoint: projects.sessions.show

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

---

## Annotations

All user annotations for a given session from a project

### Endpoint: projects.sessions.annotations.index

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

### Endpoint: projects.sessions.annotations.create

`POST: /api/projects/<int:pid>/sessions/<string:sid>/annotations/``

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
- `CONTENT_REQUIRED`: ??
- `CONTENT_IS_NOT_STRING`: ??
- `CONTENT_IS_EMPTY`: ??
- `START_INTERVAL_REQUIRED`: ??
- `START_INTERVAL_IS_NOT_INT`: ??
- `START_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `END_INTERVAL_REQUIRED`: ??
- `END_INTERVAL_IS_NOT_INT`: ??
- `END_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `START_BEFORE_END`: ??
- `TAGS_IS_NOT_LIST`: ??
- `TAG_IS_NOT_INT`: ??

## ACTIONS on an annotation

A specific annotation for a given session from a project

### Endpoint: projects.sessions.annotations.show

`GET: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`

- **NOT IMPLEMENTED:** is this endpoint useful?

### Endpoint: projects.sessions.annotations.update

`PUT: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`

> Updates an annotation on a session recording

**Arguments**

```json
    {
        "content": "Now updating",
        "start_interval": 20,
        "end_interval": 20,
        "tags": []
    }
```

Note: the `tags` argument is currently optional (so can be not sent in the request); if an empty list is sent, then all tags are
removed.

**Returns**

The modified annotation object:

```json
    {
        "comments": [],
        "content": "Now updating",
        "created_on": "08-Mar-2018",
        "end_interval": 20,
        "id": 6,
        "labels": [],
        "session_id": "1cee9eca335b45bf82a6886e424c9e86",
        "start_interval": 20,
        "tags": [],
        "updated_on": "08-Mar-2018",
        "user_id": 30
    }
```

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ?
- `SESSION_UNKNOWN`: ?
- `SESSION_NOT_IN_PROJECT`: ?
- `GENERAL_UNKNOWN_JWT_USER`: ?
- `PROJECT_UNAUTHORIZED`: ?
- `ANNOTATION_404`: ?
- `GENERAL_INVALID_JSON`:?
- `CONTENT_REQUIRED`: ??
- `CONTENT_IS_NOT_STRING`: ??
- `CONTENT_IS_EMPTY`: ??
- `START_INTERVAL_REQUIRED`: ??
- `START_INTERVAL_IS_NOT_INT`: ??
- `START_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `END_INTERVAL_REQUIRED`: ??
- `END_INTERVAL_IS_NOT_INT`: ??
- `END_INTERVAL_MUST_BE_POSITIVE_INT`: ??
- `START_BEFORE_END`: ??
- `TAGS_IS_NOT_LIST`: ??
- `TAG_IS_NOT_INT`: ??

### Endpoint

`ELETE: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[D`

> Deletes a users annotation on a session recording. Only users who created the annotation can delete it.

**Returns**

- Custom response where `meta.success` is True if the annotation was deleted, otherwise an error below is provided.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER` ??
- `PROJECT_UNAUTHORIZED`: ??
- `ANNOTATION_404`: ??
- `NOT_ANNOTATION_CREATOR`: ??

---

## Comments on an Annotation

User comments on other (or their own) annotations on a recording

### Endpoint: projects.sessions.annotations.comments.index

`GET: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/`

- **NOT IMPLEMENTED:** if you want comments for an annotation see `/annotations/<int:aid>/[GET]`

### Endpoint: projects.sessions.annotations.comments.create

`POST: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/``

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

---

## ACTIONS on comments

Users who have created a comment can fetch, edit or delete them.

### Endpoint: projects.sessions.annotations.comments.show

`GET: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`

> Retrieves a specific comment of an annotation.

**Returns**

- The comment as an object; `parent_id` is `null` if it is a comment

```json
    {
        "annotation_id": 1,
        "content": "no you",
        "created_on": "03-Mar-2018",
        "creator": {
            "fullname": "Jay Rainey",
            "user_id": 1
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

### Endpoint: projects.sessions.annotations.comments.update

`PUT: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`

> Update the content of a comment, i.e. via an `edit` feature

**Arguments**

- `content` the same argument as `POST` for a comment to an annotation above.

**Returns**

- The updated comment object as above.

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `COMMENT_404`: ??
- `COMMENT_NOT_IN_SESSION`: ??
- `GENERAL_INVALID_JSON`: ??
- `NOT_COMMENT_CREATOR`: ??
- `USER_COMMENT_CONTENT_KEY_REQUIRED`: ??
- `USER_COMMENT_IS_NOT_STRING`: ??

### Endpoint: projects.sessions.annotations.comments.create

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

### Endpoint: project.sessions.annotations.comments.destroy

`DELETE: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`

> Soft-deletes the entire comment, i.e. via an `delete` feature

**Returns**

- `204` no content status code

**Errors**

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??
- `COMMENT_404`: ??
- `COMMENT_NOT_IN_SESSION`: ??
- `NOT_COMMENT_CREATOR`: ??
