from ..models.projects import Project
from ..utils.general import CustomException
from ..models.user import User
from ..models.projects import InterviewSession, ConnectionComments
from flask_jwt_extended import get_jwt_identity


def abort_if_not_admin_or_staff(user, project_id, action="UPDATE"):
    role = user.role_for_project(project_id)
    if not role or role == 'user':
        raise CustomException(403, errors=[('%s_UNAUTHORIZED' % action)])


def abort_on_unknown_project_id(pid):
    if pid not in [p.id for p in Project.query.all()]:
        raise CustomException(400, errors=['PROJECT_DOES_NOT_EXIST'])


def abort_if_session_not_in_project(session, pid):
    if session.project_id != pid:
        raise CustomException(401, errors=['SESSION_NOT_IN_PROJECT'])


def abort_if_not_a_member_and_private(user, project):
    if not user or not user.is_project_member(project.id) and not project.is_public:
        raise CustomException(401, errors=['PROJECT_UNAUTHORIZED'])


def abort_if_not_project_member(user, project_id):
    if not user.is_project_member(project_id):
        raise CustomException(401, errors=['MEMBERSHIP_NOT_EXISTS'])


def abort_if_project_member(user, project_id):
    if user.is_project_member(project_id):
        raise CustomException(401, errors=['MEMBERSHIP_EXISTS'])


def abort_if_unknown_project(project):
    if not project:
        raise CustomException(400, errors=['PROJECT_404'])


def abort_if_unknown_session(session):
    if not session:
        raise CustomException(401, errors=['SESSION_404'])


def abort_if_unknown_user(user):
    if not user or user.email not in [user.email for user in User.query.all()]:
        raise CustomException(400, errors=['GENERAL_UNKNOWN_USER'])


def abort_if_unknown_comment(cid, aid):
    if cid not in [i.id for i in ConnectionComments.query.all()]:
        raise CustomException(400, errors=['COMMENTS_404'])

    if aid != ConnectionComments.query.get(cid).connection_id:
        raise CustomException(400, errors=['COMMENTS_NOT_IN_SESSION'])


def jsonify_request_or_abort():
    from flask import request
    data = request.get_json(force=True, silent=True)
    abort_if_invalid_json(data)
    return data


def abort_if_invalid_json(data):
    if not data:
        raise CustomException(400, errors=['GENERAL_INVALID_JSON'])


def abort_if_errors_in_validation(errors):
    if errors:
        raise CustomException(400, errors=errors)


def abort_if_unknown_annotation(annotation):
    if not annotation:
        raise CustomException(400, errors=['ANNOTATIONS_404'])


def abort_if_not_user_made(user_id, user_of_annotation):
    if user_id != user_of_annotation:
        raise CustomException(400, errors=['ANNOTATIONS_NOT_CREATOR'])


def abort_if_not_user_made_comment(user_id, user_of_comment):
    if user_id != user_of_comment:
        raise CustomException(400, errors=['COMMENTS_NOT_CREATOR'])


def abort_if_unauthorized(project):
    """
    Can return the following:

        - GENERAL_UNKNOWN_USER
        - PROJECT_UNAUTHORIZED
    """
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    abort_if_unknown_user(user)
    abort_on_unknown_project_id(project.id)
    abort_if_not_a_member_and_private(user, project)
    return user


def abort_if_invalid_parameters(pid, sid):
    """
    Can return the following:

        - PROJECT_DOES_NOT_EXIST
        - SESSION_UNKNOWN
        - SESSION_NOT_IN_PROJECT
    """
    abort_on_unknown_project_id(pid)
    sess = InterviewSession.query.get(sid)
    abort_if_unknown_session(sess)
    abort_if_session_not_in_project(sess, pid)

