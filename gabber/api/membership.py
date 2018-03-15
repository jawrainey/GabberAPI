# -*- coding: utf-8 -*-
"""
An administrator can invite or remove members from their project.
These actions are notified to users once carried out.
"""
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from gabber.api.schemas.project import ProjectMember
from gabber.api.schemas.membership import AddMemberSchema
from gabber.projects.models import Project
from gabber.projects.models import Membership, Roles
from gabber.users.models import User
from gabber.utils.general import custom_response, CustomException
from gabber import db
import gabber.api.helpers as helpers
import gabber.utils.email as email_client


class ProjectInvites(Resource):
    @jwt_required
    def post(self, pid):
        """
        An administrator or staff member of a project invited a user

        Mapped to: /api/project/<int:id>/membership/invites/
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

            if user.registered:
                email_client.send_project_member_invite_registered_user(admin, user, project)
            else:
                email_client.send_project_member_invite_unregistered_user(admin, user, project)
        else:
            return custom_response(400, errors=['PROJECT_MEMBER_EXISTS'])
        return custom_response(200, data=ProjectMember().dump(membership))

    @jwt_required
    def delete(self, pid, mid):
        """
        Removes a user and emails them that they have been removed from a project and by whom.

        Mapped to: /api/project/<int:id>/membership/invites/<int:mid>
        """
        helpers.abort_if_unauthorized(Project.query.get(pid))
        admin = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(admin)
        helpers.abort_if_not_admin_or_staff(admin, pid, "INVITE_MEMBER")
        membership = Membership.query.filter_by(id=mid).first()
        if not membership:
            raise CustomException(400, errors=['UNKNOWN_MEMBERSHIP'])
        elif membership.deactivated:
            raise CustomException(400, errors=['USER_ALREADY_DELETED'])
        membership.deactivated = True
        db.session.commit()
        email_client.send_project_member_removal(admin, User.query.get(membership.user_id), Project.query.get(pid))
        return custom_response(200, data=ProjectMember().dump(membership))

    @staticmethod
    def validate_and_get_data(project_id):
        """
        Helper method as PUT/DELETE required the same validation.
        """
        helpers.abort_if_unauthorized(Project.query.get(project_id))
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, project_id, "INVITE_MEMBER")
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
        email_client.send_project_member_joined(user, project)
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
        email_client.send_project_member_left(user, project)
        membership = Membership.leave_project(user.id, pid)
        return custom_response(200, data=ProjectMember().dump(membership))
