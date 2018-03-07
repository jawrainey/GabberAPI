from gabber.projects.models import Project
from gabber.utils.general import CustomException
from gabber.users.models import User


def abort_if_not_admin_or_staff(user, project_id, action="UPDATE"):
    role = user.role_for_project(project_id)
    if not role or role == 'user':
        raise CustomException(403, errors=[('PROJECT_%s_UNAUTHORIZED' % action)])


def abort_on_unknown_project_id(pid):
    if pid not in [p.id for p in Project.query.all()]:
        raise CustomException(404, errors=['PROJECT_DOES_NOT_EXIST'])


def abort_if_not_a_member_and_private(user, project):
    if not user.is_project_member(project.id) and not project.isProjectPublic:
        raise CustomException(401, errors=['PROJECT_UNAUTHORIZED'])


def abort_if_unknown_project(project):
    if not project:
        raise CustomException(404, errors=['PROJECT_UNKNOWN'])


def abort_if_unknown_session(session):
    if not session:
        raise CustomException(401, errors=['SESSION_UNKNOWN'])


def abort_if_unknown_user(user):
    if not user or user.email not in [user.email for user in User.query.all()]:
        raise CustomException(400, errors=['GENERAL_UNKNOWN_JWT_USER'])


def abort_if_invalid_json(data):
    if not data:
        raise CustomException(400, errors=['GENERAL_INVALID_JSON'])


def abort_if_data_pid_not_route_pid(request_pid, route_pid):
    if request_pid != route_pid:
        raise CustomException(400, errors=['GENERAL_REQUEST_DATA_ID_INVALID'])


def abort_if_errors_in_validation(errors):
    if errors:
        raise CustomException(400, errors=errors)
