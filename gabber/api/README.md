# API Documentation: work in progress

All requests are returned in the following format where errors contains unique _keys_ to simplify frontend access:

    {
        "data": [],
        "meta: {
            errors: [
            "AUTH_USER_UNKNOWN", 
            "PROJECTS_TITLE_EXISTS"
            ],
            success: True/False
        }
    }

**Note:** all `POST/PUT/DELETE` requests must be in `json` format.

The following are general errors that can be returned across resources:

- `GENERAL_INVALID_JSON`: The request made contains invalid JSON
- `GENERAL_UNKNOWN_USER`: The user in the JWT request does not exist.

### Authentication

#### Endpoint: /api/auth/register/`[POST]`

**Description:** 

- Create a new user and returns a JWT

**Arguments**

- `fullname`: the full name of a user, or what they consider their display name to be. This is **not** validated as 
fullname varies across countries, where some consider middle name, etc.
- `email`: must be a valid email address and is used to uniquely identify a user.
- `password`: must be at least 12 characters.

**Returns:**


    { 
      "access_token": "",
      "refresh_token": ""
    }


**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_FULLNAME_REQUIRED`: A full name is required to register. This is for others to identify you.
- `AUTH_EMAIL_DOES_NOT_EXIST`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long


---

#### Endpoint: /api/auth/login/`[POST]`

**Description** 

- authenticates a known user and returns a JWT

**Arguments**

- `email`: Must be a valid email address and is used to uniquely identify a user.
- `password`: Must be at least 12 characters.

**Returns:**


    { 
      "access_token": "",
      "refresh_token": ""
    }

**Errors**

- `AUTH_INCORRECT_PASSWORD`: The password you provided for that email is invalid.
- `AUTH_EMAIL_EXISTS`: A user with that account does not exist.
- `AUTH_EMAIL_REQUIRED`: An email address is required to register. This is your username.
- `AUTH_INVALID_EMAIL`: The email address provided is invalid.
- `AUTH_PASSWORD_REQUIRED`: A password is required to register
- `AUTH_INCORRECT_PASSWORD`: An incorrect password was provided for this email address.
- `AUTH_PASSWORD_LENGTH`: The password must be at least 12 characters long

---

#### Endpoint: /api/auth/forgot/`[POST]`

**Description** 

- Emails a user with a time serialized URL that can be used to reset their password

**Arguments**

- `email`: the email address of the user to reset the password for

**Returns**

- Empty custom response where `success` if True if the email has been sent, otherwise False.

**Actions**

- Emails a _unique_ [timed serializer URL](http://pythonhosted.org/itsdangerous/) (i.e. token) to reset password

**Errors**:

- `GENERAL_INVALID_JSON`: The request you made contains invalid JSON.
- `EMAIL_NOT_FOUND`: The email address provided does not belong to a known user.
- `MUST_BE_EMAIL`: You have not provided a valid email address.
- `ISSUE_SENDING_EMAIL`: An error occurred when trying to send the email. If this continues, please get in touch.

#### Endpoint: /api/auth/reset/<token>/`[GET]`

**Description** 

- Returns the email address associated with that token if a token is valid, which
can be used on the frontend to pre-populate fields, etc.

**Arguments** 

- N/A

**Returns**

    { 
      "email": "jawrainey@gmail.com"
    }

**Errors**:

- `TOKEN_404:` ???

#### Endpoint: /api/auth/reset/`[POST]`

**Description** 

- Changes password of a given email if the token sent is also valid.

**Arguments**

- `email`: the email address of the user to reset
- `password`: the password to change the email address to
- `token`: the token from the email that was sent

**Returns**

The same response as login/register:

    { 
      "access_token": "",
      "refresh_token": ""
    }

**Errors**:

- `TODO:` ???

---

### Projects

#### Endpoint /api/projects/`[GET]`

**Description** 

- A dictionary of personal/public projects for a user. If the user is unauthenticated, then the private list is empty.

**Returns**

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
                    ...
                ],
                "updated_on": "04-Mar-2018"
            }
        ]
    }

**Notes** 

1) If a project is public and a user is a member then it appears in the personal list.
4) `has_consent` and `is_public` are the configuration properties of a project


**Errors**:

- `GENERAL.UNKNOWN_USER:` The user making the request does not exist, i.e. they are JWT user but unknown to our system.

---

#### Endpoint /api/projects/`[POST]`

**Description** 

- Creates a new project

**Arguments**

    {
        "title": "The title of your neat project",
        "creator": 10,
        "description": "Describe your project ...",
        "privacy": "public" or "private",
        "topics": ["Topics must strings", "Otherwise madness occurs"]
    }

**Returns**

The same format as `/projects/`, but for the individual project the user just created

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

#### Endpoint: /api/projects/<int:pid>/`[GET]`
  
  
**Description** 

- Returns a project if it is public. If it is private, data is only returned if the JWT user is a member.

**Returns** 
    
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
            ...
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
            ...
        ],
        "slug": "the-title-of-your-a",
        "title": "The title of your a",
        "updated_on": "05-Mar-2018"
    }

**Errors** 

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database. 
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.

---

#### Endpoint: /api/projects/<int:pid>/`[PUT]`
  
  
**Description** 

- Updates attributes of an existing project

**Arguments** 

Same `object` as when getting, creating, etc, however, the `topics` field must include the following attributes as
it overrides all existing topics for the project; `text` and `is_active` is required for all topics:

**Create:** if no ID is provided, then a topic is created.
**Update:** the `id`, `text` and `is_active` of the topic. The text is overridden for that topic ID.
**Delete:** The topics list must include `is_active`, which if flagged as `false` will soft-delete a topic. 

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

#### Endpoint: /api/projects/<int:pid>/`[DELETE]`
  
  
**Description** 

- Soft deletes an existing project. The JWT user must have the creator role of a project to delete it.

**Arguments** N/A
**Returns** 

- 

**Errors** 

- `PROJECT_DOES_NOT_EXIST`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_DELETE_UNAUTHORIZED`: ??

---

## Project membership 

This is partially implemented as we have yet to decide on membership; this is for when users join/leave, rather than
an admin adding/removing them, etc.  

#### Endpoint: /api/projects/<int:pid>/membership/`[POST]`

**Description** join (i.e. become a member) of an existing public project

**Returns** True if success, otherwise False within the `meta` object.

**Errors** 

- `TODO`: ??

---

#### Endpoint: /api/projects/<int:pid>/membership/`[DELETE]`

**Description** leaves a project that the user is a member of. _Note: this NOT yet implemented._

**Returns** True if success, otherwise False within the `meta` object.

**Errors** 

- `TODO`: ??

---

## Sessions

A list of sessions that have been recorded for a particular project.

#### Endpoint: /api/projects/<int:pid>/sessions/`[GET]`

**Description** 

- A list of all sessions for a given project

**Returns** 


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
                ...
            ],
            "user_annotations": []
        },
        ...
    ]


**Errors** 

- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database. 
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `SESSION_UNKNOWN`: The session you tried to view does not exist.

---

#### Endpoint: /api/projects/<int:pid>/sessions/`[POST]`

#### MOBILE SUPPORT: LEGACY

**Description** 

- Creates a new session for a given project. **Note:** this is currently only used  on the mobile device, 
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

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/`[GET]`

**Description** 

- An individual Gabber recorded session for a project

**Returns**


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
            ...
        ],
        "topics": [
            {
                "end": "8",
                "id": 1,
                "start": "0",
                "text": "Topics must be less than 280 words"
            },
            ...
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
            ...
        ]

**Errors** 
  
- `GENERAL_UNKNOWN_JWT_USER`: The JWT user is unknown to the database. 
- `PROJECT_DOES_NOT_EXIST`: The project you tried to view does not exist.
- `PROJECT_UNAUTHORIZED`: You are unauthorized to view this project.
- `SESSION_UNKNOWN`: The session you tried to view does not exist.

---

## Annotations

All user annotations for a given session from a project

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/`[GET]`

**Description** 

- A list of user annotations on a recording session

**Returns** 

Note: 

1) `replies` currently returns a list of IDs of other comments on this comment. I will update
this once I get recursive serialization working as comments are self referential.
2) `labels` and `tags` present the same information, whereas `tags` only contains the IDs of tags, which
simplifies updating the model.


    [
        {
            "comments": [
                {
                    "connection": 1,
                    "created_on": "03-Mar-2018",
                    "id": 1,
                    "parent_id": 1,
                    "replies": [
                        1,
                        2
                    ],
                    "text": "Top comment",
                    "updated_on": "03-Mar-2018",
                    "user_id": 1
                },
                {
                    "connection": 1,
                    "created_on": "03-Mar-2018",
                    "id": 3,
                    "parent_id": 1,
                    "replies": [],
                    "text": "A respond to",
                    "updated_on": "03-Mar-2018",
                    "user_id": 1
                }
            ],
            "content": "Hello world",
            "created_on": "04-Mar-2018",
            "end_interval": 10,
            "id": 1,
            "labels": [
                {
                    "id": 1,
                    "text": "tag one"
                },
                {
                    "id": 2,
                    "text": "tag two"
                },
                {
                    "id": 3,
                    "text": "faith"
                }
            ],
            "tags": [1,2,3],
            "session_id": "1cee9eca335b45bf82a6886e424c9e86",
            "start_interval": 3,
            "updated_on": "08-Mar-2018",
            "user_id": 1
        },
        ...
    ]
    

**Errors** 

- `PROJECT_DOES_NOT_EXIST`: ??
- `SESSION_UNKNOWN`: ??
- `SESSION_NOT_IN_PROJECT`: ??
- `GENERAL_UNKNOWN_JWT_USER`: ??
- `PROJECT_UNAUTHORIZED`: ??

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/`[POST]`

**Description** 

- Creates a new user annotation on a session recording

**Arguments** 

    {
        "content": "Now updating",
        "start_interval": 20,
        "end_interval": 20,
        "tags": [1,2]
    }


Note: the `tags` argument is currently optional (so can be not sent in the request); if an empty list is sent, then all tags are
removed.

**Returns** 

- The created annotation object, e.g.

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

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[GET]`

- **NOT IMPLEMENTED:** is this endpoint useful?

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[PUT]`

**Description** 

- Updates an annotation on a session recording

**Arguments** 

    {
        "content": "Now updating",
        "start_interval": 20,
        "end_interval": 20,
        "tags": []
    }

Note: the `tags` argument is currently optional (so can be not sent in the request); if an empty list is sent, then all tags are
removed.

**Returns** 

The modified annotation object:

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

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[DELETE]`

**Description** 

- Deletes a users annotation on a session recording. Only users who created the annotation can delete it.

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

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/`[GET]`

**Description**
**Returns** 
**Errors** 

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/`[POST]`

**Description** 
**Arguments**
**Returns**
**Errors** 

---

## ACTIONS on comments

Users who have created a comment can fetch, edit or delete them.

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`[GET]`

**Description**
**Returns** 
**Errors** 

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`[PUT]`

**Description**
**Returns** 
**Errors**

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/`[DELETE]`

**Description**
**Returns** 
**Errors**