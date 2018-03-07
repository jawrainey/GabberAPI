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

#### Endpoint: /api/auth/reset_password/`[PUT]`

**Description** 

- emails a user with a `magic URL` to reset their password

**Arguments**

- `email`: the email address of the user to reset

**/api/auth/reset_password/**
**/api/users/<int:uid>/reset_password/**

**Returns**

- TODO

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
                    "id": 13,
                    "name": "Jay Rainey"
                },
                "description": "new desc",
                "id": 2,
                "isConsentEnabled": false,
                "isProjectPublic": true,
                "members": [
                    {
                        "id": 13,
                        "name": "Jay Rainey",
                        "role": "admin",
                        "user": 13
                    },
                    {
                        "id": 14,
                        "name": "Edward Jenkins",
                        "role": "user",
                        "user": 14
                    }
                ],
                "prompts": [
                    {
                        "created_on": "04-Mar-2018",
                        "id": 3,
                        "image_path": "default.jpg",
                        "is_active": 1,
                        "project": 2,
                        "text_prompt": "one topic lol",
                        "updated_on": "04-Mar-2018"
                    },
                    ...
                ],
                "slug": "ni-oal",
                "title": "ni oal",
                "topics": [
                    {
                        "created_on": "04-Mar-2018",
                        "id": 3,
                        "image_path": "default.jpg",
                        "is_active": 1,
                        "project": 2,
                        "text_prompt": "one topic lol",
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
2) `prompt` mirrors `topics` for backwards comparability with mobile application. This is temporary. **Always use topics**
3) `imageURL` is a deprecated from when topics also supported images.
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
            "id": 22,
            "name": "jay rainey"
        },
        "description": "new desc",
        "id": 11,
        "isConsentEnabled": false,
        "isProjectPublic": true,
        "members": [
            {
                "id": 22,
                "name": "jay rainey",
                "role": "admin",
                "user": 22
            }
        ],
        "prompts": [
            {
                "created_on": "05-Mar-2018",
                "id": 14,
                "image_path": "default.jpg",
                "is_active": 1,
                "project": 11,
                "text_prompt": "topics",
                "updated_on": "05-Mar-2018"
            }
        ],
        "slug": "super-new-title",
        "title": "Super new title",
        "topics": [
            {
                "created_on": "05-Mar-2018",
                "id": 14,
                "image_path": "default.jpg",
                "is_active": 1,
                "project": 11,
                "text_prompt": "topics",
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
            "id": 1,
            "name": "Jay Rainey"
        },
        "description": "Describe your project in at most 230 words",
        "id": 1,
        "isConsentEnabled": false,
        "isProjectPublic": true,
        "members": [
            {
                "id": 1,
                "name": "Jay Rainey",
                "role": "user",
                "user": 1
            }
            ...
        ],
        "prompts": [
            {
                "created_on": "03-Mar-2018",
                "id": 1,
                "image_path": "default.jpg",
                "is_active": 0,
                "project": 1,
                "text_prompt": "Topics must be less than 280 words",
                "updated_on": "03-Mar-2018"
            }
            ...
        ],
        "slug": "the-title-of-your-a",
        "title": "The title of your a",
        "topics": [
            {
                "created_on": "03-Mar-2018",
                "id": 1,
                "image_path": "default.jpg",
                "is_active": 0,
                "project": 1,
                "text_prompt": "Topics must be less than 280 words",
                "updated_on": "03-Mar-2018"
            }
            ...
        ],
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

- `TODO`: 

**Returns** 

- The updated, serialized project as in `GET` containing the updated details.

**Errors** 

- `TODO`: ?

---

#### Endpoint: /api/projects/<int:pid>/`[DELETE]`
  
  
**Description** 

- Soft deletes an existing project. The JWT user must have the creator role of a project to delete it.

**Arguments** N/A
**Returns** N/A
**Errors** 

- `TODO`: ??

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
                "created_on": "03-Mar-2018",
                "creator": {
                    "id": 6,
                    "name": "Jay"
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
                        "interview": "1cee9eca335b45bf82a6886e424c9e86",
                        "justification": "first annotation",
                        "start_interval": 0,
                        "updated_on": "04-Mar-2018",
                        "user": 1
                    },
                    ...
                ]
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

    {
        "created_on": "03-Mar-2018", 
        "creator": {
            "id": 6, 
            "name": "Jay"
        }, 
        "id": "1cee9eca335b45bf82a6886e424c9e86", 
        "participants": [
            {
                "name": "Jay", 
                "role": "interviewer", 
                "user_id": 6
            }, 
            {
                "name": "Hey", 
                "role": "interviewee", 
                "user_id": 7
            }
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
                "interview": "1cee9eca335b45bf82a6886e424c9e86", 
                "justification": "first annotation", 
                "start_interval": 0, 
                "updated_on": "04-Mar-2018", 
                "user": 1
            }, 
            ...
        ]
    }

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

- gets a list of user annotations on a session recording

**Returns** 

- `True` if success, otherwise `False` within the `meta` object.

**Errors** 

- `TODO`: ??

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/`[POST]`

**Description** 

- Creates a new user annotation on a session recording

**Arguments** 
**Returns** 
**Errors**  

## ACTIONS on an annotation

A specific annotation for a given session from a project

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[GET]`

**Description** 

- A specific annotation for a given session

**Returns** 
**Errors** 

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[PUT]`

**Description** 

- Updates an annotation on a session recording

**Returns** 
**Errors**  

#### Endpoint: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/`[DELETE]`

**Description** 

- Deletes a users annotation on a session recording. Only users who creates the annotation can delete it.

**Returns** 
**Errors** 

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