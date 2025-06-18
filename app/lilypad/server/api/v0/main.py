"""The `/api/v0` FastAPI sub-app for `lilypad`."""

from fastapi import FastAPI

from ....ee.server.api import v0_ee_router
from .api_keys_api import api_keys_api
from .auth import auth_router
from .billing_api import billing_router
from .comments_api import comments_router
from .environments_api import environments_router
from .external_api_keys_api import external_api_key_router
from .functions_api import functions_router
from .organization_invites_api import organization_invites_router
from .organizations_api import organization_router
from .projects_api import projects_router
from .settings_api import settings_router
from .spans_api import spans_router
from .tags_api import tags_router
from .traces_api import traces_router
from .user_consents_api import user_consents_router
from .users_api import users_router

api = FastAPI(separate_input_output_schemas=False)
# The `/ee` FastAPI sub-app for `lilypad`.
api.include_router(v0_ee_router)
api.include_router(api_keys_api)
api.include_router(billing_router)
api.include_router(functions_router)
api.include_router(organization_invites_router)
api.include_router(projects_router)
api.include_router(spans_router)
api.include_router(traces_router)
api.include_router(auth_router)
api.include_router(users_router)
api.include_router(organization_router)
api.include_router(external_api_key_router)
api.include_router(environments_router)
api.include_router(user_consents_router)
api.include_router(tags_router)
api.include_router(comments_router)
api.include_router(settings_router)


__all__ = ["api"]
