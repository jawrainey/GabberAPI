from gabber.projects.models import Project
from gabber.utils.general import CustomException
from gabber.users.models import User
from gabber.projects.models import InterviewSession
from flask_jwt_extended import get_jwt_identity


def abort_if_not_admin_or_staff(user, project_id, action="UPDATE"):
    role = user.role_for_project(project_id)
    if not role or role == 'user':
        raise CustomException(403, errors=[('PROJECT_%s_UNAUTHORIZED' % action)])


def abort_on_unknown_project_id(pid):
    if pid not in [p.id for p in Project.query.all()]:
        raise CustomException(404, errors=['PROJECT_DOES_NOT_EXIST'])


def abort_if_session_not_in_project(session, pid):
    if session.project_id != pid:
        raise CustomException(401, errors=['SESSION_NOT_IN_PROJECT'])


def abort_if_not_a_member_and_private(user, project):
    if not user.is_project_member(project.id) and not project.is_public:
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


def abort_if_unknown_annotation(annotation):
    if not annotation:
        raise CustomException(400, errors=['ANNOTATION_404'])


def abort_if_not_user_made(user_id, user_of_annotation):
    if user_id != user_of_annotation:
        raise CustomException(400, errors=['NOT_ANNOTATION_CREATOR'])


def abort_if_unauthorized(project):
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    abort_if_unknown_user(user)
    abort_if_not_a_member_and_private(user, project)


def abort_if_invalid_parameters(pid, sid):
    abort_on_unknown_project_id(pid)
    sess = InterviewSession.query.get(sid)
    abort_if_unknown_session(sess)
    abort_if_session_not_in_project(sess, pid)

