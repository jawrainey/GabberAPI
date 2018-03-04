from flask_restful import abort
from gabber.projects.models import Project


def abort_if_empty(item):
    if not item or len(item) <= 0:
        abort(404, message='The X you have provided is empty')
    return item


def abort_if_not_admin_or_staff(user, project_id, action="UPDATE"):
    role = user.role_for_project(project_id)
    if not role or role == 'user':
        abort(403, message="You do not have permission to %s" % action)


def abort_on_unknown_project_id(pid):
    if pid not in [p.id for p in Project.query.all()]:
        abort(404, message="The project that you tried to view does not exist")


def abort_if_unknown_user(user):
    if not user:
        abort(400, message='The user making the request does not exist')


def abort_if_unknown_project(project):
    if not project:
        abort(400, message='That project does not exist')


def abort_if_unknown_session(session):
    if not session:
        abort(400, message='That session does not exist')


def abort_if_not_a_member_and_private(user, project):
    if not user.is_project_member(project.id) and not project.isProjectPublic:
        abort(401, message='You are not a member of this project')
