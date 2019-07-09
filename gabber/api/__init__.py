from flask_restful import Api

restful_api = Api()

from .help import SupportedLanguages
from .fcm import TokenForUser
from .playlist import Playlist
from .playlists import Playlists
from .projects import Projects
from .project import Project
from .membership import ProjectMembership, ProjectInvites, ProjectInviteVerification
from .sessions import ProjectSessions, Recommendations
from .session import ProjectSession
from .consent import SessionConsent
from .annotations import UserAnnotations, UserAnnotation
from .comments import Comments, Comment, CommentsReplies
from .auth import TokenRefresh, UserRegistration, UserLogin, ForgotPassword, ResetPassword, UserAsMe
from .auth import VerifyRegistration
from .misc import SearchImages

restful_api.add_resource(SearchImages, '/api/misc/photos/')
restful_api.add_resource(SupportedLanguages, '/api/help/languages/')
restful_api.add_resource(TokenForUser, '/api/fcm/')
restful_api.add_resource(Projects, '/api/projects/')
restful_api.add_resource(Project, '/api/projects/<int:pid>/')
restful_api.add_resource(Playlists, '/api/playlists/')
restful_api.add_resource(Playlist, '/api/playlists/<int:pid>/')
restful_api.add_resource(ProjectMembership, '/api/projects/<int:pid>/membership/')
restful_api.add_resource(ProjectInvites,
                         '/api/projects/<int:pid>/membership/invites/',
                         '/api/projects/<int:pid>/membership/invites/<int:mid>/')
restful_api.add_resource(ProjectInviteVerification, '/api/projects/invites/<token>/')
restful_api.add_resource(Recommendations, '/api/sessions/recommendations/')
restful_api.add_resource(ProjectSessions, '/api/projects/<int:pid>/sessions/')
restful_api.add_resource(ProjectSession, '/api/projects/<int:pid>/sessions/<string:sid>/')
restful_api.add_resource(SessionConsent, '/api/consent/<string:token>/')
restful_api.add_resource(UserAnnotations, '/api/projects/<int:pid>/sessions/<string:sid>/annotations/')
restful_api.add_resource(UserAnnotation, '/api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/')
restful_api.add_resource(Comments, '/api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/')
restful_api.add_resource(Comment, '/api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/')
restful_api.add_resource(CommentsReplies, '/api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/replies/')
restful_api.add_resource(TokenRefresh, '/api/auth/token/refresh/')
restful_api.add_resource(UserAsMe, '/api/auth/me/')
restful_api.add_resource(VerifyRegistration, '/api/auth/verify/<string:token>/')
restful_api.add_resource(UserRegistration, '/api/auth/register/')
restful_api.add_resource(UserLogin, '/api/auth/login/')
restful_api.add_resource(ForgotPassword, '/api/auth/forgot/')
restful_api.add_resource(ResetPassword, '/api/auth/reset/')
