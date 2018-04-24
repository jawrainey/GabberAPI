# -*- coding: utf-8 -*-
"""
An administrator can invite or remove members from their project.
These actions are notified to users once carried out.
"""
from ..api.auth import create_jwt_access, AuthToken
from ..api.schemas.auth import UserSchemaHasAccess
from ..api.schemas.membership import AddMemberSchema, ProjectInviteWithToken
from ..api.schemas.project import ProjectMember, ProjectMemberWithAccess, ProjectModelSchema
from ..models.projects import Project
from ..models.projects import Membership, Roles
from ..models.user import User
from ..utils.general import custom_response, CustomException
from .. import db
from flask import current_app as app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer
import gabber.utils.helpers as helpers
import gabber.utils.email as email_client


class ProjectInviteVerification(Resource):
    """
    Mapped to: /api/projects/invites/<token>/
    """
    @staticmethod
    def get(token):
        """
        Provides details of a user (fullname & email) and the project (ID) they were invited to.
        """
        token_data = AuthToken.validate_token(token)
        user = User.query.get(token_data['user_id'])
        project = Project.query.get(token_data['project_id'])
        payload = dict(user=UserSchemaHasAccess().dump(user), project=ProjectModelSchema().dump(project))
        return custom_response(200, data=payload)

    @staticmethod
    def put(token):
        """
        Updates an unconfirmed user record* and accepts the membership invite.
        *i.e. someone created through a Gabber or when invited
        """
        token_data = AuthToken.validate_token(token)
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ProjectInviteWithToken().validate(data))

        user = User.query.get(token_data['user_id'])
        user.fullname = data['fullname']
        user.set_password(data['password'])
        user.registered = True
        user.verified = True

        membership = Membership.query.filter_by(project_id=token_data['project_id'], user_id=user.id).first()
        # Makes sure that they can only be confirmed once
        if membership.confirmed:
            return custom_response(400, errors=['MEMBERSHIP_CONFIRMED'])

        membership.confirmed = True
        db.session.commit()
        return custom_response(200, data=create_jwt_access(user.email))

    @staticmethod
    def generate_invite_url(user_id, project_id):
        """
        Generates an invite URL with embedded information
        """
        # Only embed necessary information for lookup on the GET
        payload = {'user_id': user_id, 'project_id': project_id}
        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(payload, app.config['SALT'])
        # Do not store tokens as: (1) they're one time use and (2) token expires.
        return '{}/accept/{}/'.format(app.config['WEB_HOST'], token)


class ProjectInvites(Resource):
    @jwt_required
    def post(self, pid, mid=None):
        """
        An administrator or staff member of a project invited a user

        Mapped to: /api/projects/<int:id>/membership/invites/
        """
        admin, data = self.validate_and_get_data(pid)
        helpers.abort_if_errors_in_validation(AddMemberSchema().validate(data))
        user = User.query.filter_by(email=data['email']).first()
        # Note: If the user is not known an unregistered user is created.
        # This is similar to how users are created after a Gabber session.
        if not user:
            user = User.create_unregistered_user(data['fullname'], data['email'])
        # The user cannot be added to the same project multiple times
        if not user.is_project_member(pid):
            membership = Membership(uid=user.id,  pid=pid, rid=Roles.user_role(), confirmed=user.registered)
            db.session.add(membership)
            db.session.commit()

            project = Project.query.get(pid)

            if user.registered or user.verified:
                email_client.send_project_member_invite_registered_user(admin, user, project)
            else:
                email_client.send_project_member_invite_unregistered_user(admin, user, project)
        else:
            return custom_response(400, errors=['MEMBERSHIP_MEMBER_EXISTS'])
        return custom_response(200, data=ProjectMemberWithAccess().dump(membership))

    @jwt_required
    def delete(self, pid, mid=None):
        """
        Removes a user and emails them that they have been removed from a project and by whom.

        Mapped to: /api/project/<int:id>/membership/invites/<int:mid>
        """
        if not mid:
            raise CustomException(400, errors=['membership.NOT_EXISTS'])

        helpers.abort_if_unauthorized(Project.query.get(pid))
        admin = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(admin)
        helpers.abort_if_not_admin_or_staff(admin, pid, "membership.INVITE")
        membership = Membership.query.filter_by(id=mid).first()

        if not membership:
            raise CustomException(400, errors=['membership.UNKNOWN'])
        elif membership.deactivated:
            raise CustomException(400, errors=['membership.USER_DEACTIVATED'])
        membership.deactivated = True
        db.session.commit()
        email_client.send_project_member_removal(admin, User.query.get(membership.user_id), Project.query.get(pid))
        return custom_response(200, data=ProjectMemberWithAccess().dump(membership))

    @staticmethod
    def validate_and_get_data(project_id):
        """
        Helper method as PUT/DELETE required the same validation.
        """
        helpers.abort_if_unauthorized(Project.query.get(project_id))
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, project_id, "membership.INVITE")
        data = helpers.jsonify_request_or_abort()
        return user, data


class ProjectMembership(Resource):
    """
    Mapped to: /api/project/<int:id>/membership/
    """
    @jwt_required
    def post(self, pid):
        """
        Joins a public project for a given user (determined through JWT token)
        """
        project = Project.query.get(pid)
        user = helpers.abort_if_unauthorized(project)
        helpers.abort_if_project_member(user, pid)
        membership = Membership.join_project(user.id, pid)
        return custom_response(200, data=ProjectMember().dump(membership))

    @jwt_required
    def delete(self, pid):
        """
        Leaves a project for a given user (determined through JWT token)
        """
        project = Project.query.get(pid)
        user = helpers.abort_if_unauthorized(project)
        if not user.is_project_member(pid):
            helpers.abort_if_not_project_member(user, pid)
        membership = Membership.leave_project(user.id, pid)
        return custom_response(200, data=ProjectMember().dump(membership))
