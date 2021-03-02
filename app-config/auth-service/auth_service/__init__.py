try:
    from contextlib import asynccontextmanager
except ImportError:
    # Python 3.6
    from asyncio_extras import async_contextmanager as asynccontextmanager
import json
import logging
import os
import typing

import aiohttp
from keycloak.aio.realm import KeycloakRealm
import tornado.ioloop
import tornado.web


LOG = logging.getLogger(__name__)


class BaseHandler(tornado.web.RequestHandler):
    def set_session_cookie(self, session_data: dict, expiry_in_seconds: int) -> None:
        seconds_per_day = 60 * 60 * 24
        self.set_secure_cookie(
            'session', json.dumps(session_data),
            expires_days=expiry_in_seconds / seconds_per_day,
        )

    def get_session_cookie(self) -> typing.Optional[dict]:
        session_data = json.loads(self.get_secure_cookie('session') or 'null')
        return session_data


class OIDCClientMixin:
    @asynccontextmanager
    async def get_oidc_client(self):
        """Async context manager to get hold of a OIDC client."""
        realm_params = {
            'server_url': self.settings['oicd_server'],
            'realm_name': self.settings['oicd_realm'],
        }
        oicd_params = {
            'client_id': self.settings['client_id'],
            'client_secret': self.settings['client_secret'],
        }
        async with KeycloakRealm(**realm_params) as realm:
            oidc_client = await realm.open_id_connect(**oicd_params)
            yield oidc_client


class Login(BaseHandler):
    async def get(self):
        # Initiate the OICD flow.
        return self.redirect('/auth/authenticate')


class Authentication(BaseHandler, OIDCClientMixin):
    async def get(self):
        async with self.get_oidc_client() as oidc_cli:
            redirect_uri = f'{self.request.protocol}://{self.request.host}/auth/authorize'
            LOG.info(f'Redirecting to the authorization url. Will return to {redirect_uri}')
            return self.redirect(oidc_cli.authorization_url(redirect_uri=redirect_uri))


class Authorization(BaseHandler, OIDCClientMixin):
    async def get(self):
        code = self.get_argument('code', None)
        if code is None:
            # Somebody is hitting this endpoint without going through the proper
            # flow. Let's start again.
            return self.redirect('/auth/authenticate')

        async with self.get_oidc_client() as oidc_cli:
            redirect_uri = f'{self.request.protocol}://{self.request.host}/auth/authorize'

            try:
                LOG.info(f'Validating the authorization code')
                result = await oidc_cli.authorization_code(code, redirect_uri=redirect_uri)
            except aiohttp.client_exceptions.ClientConnectionError:
                LOG.error(f'There was a problem validating the authorization code')
                self.set_status(401)
                # Happens when the code is no longer valid (e.g. if you re-visit a
                # url that was tracked in the browser devtools).
                self.finish('Error logging in. Would you like to <a href="/auth/login">try again?</a>')

            LOG.info(f'Fetching user info')
            user_info = await oidc_cli.userinfo(result['access_token'] or '')

            session_data = {
                'refresh_token': result['refresh_token'],
                'username': user_info.get('preferred_username', user_info['email']),
                'fullname': user_info['name'],
                'email': user_info['email'],
            }

            self.set_session_cookie(
                session_data,
                expiry_in_seconds=result['refresh_expires_in'],
            )

        LOG.info(f'User {session_data["username"]} successfully logged in. Redirecting to complete.')
        return self.redirect(f'/auth/complete')


class LoginComplete(BaseHandler):
    def get(self):
        redirect = self.get_cookie('POST_AUTH_REDIRECT')
        self.clear_cookie('POST_AUTH_REDIRECT')
        if redirect is None:
            LOG.info("Login complete. No redirect specified, redirecting to /")
            self.redirect('/')
        else:
            LOG.info(f"Login complete. Redirecting to {redirect} as was initially requested")
            self.redirect(redirect)


class ProbeAuthentication(BaseHandler):
    """A handler to return 200 if the user is logged in, and 401 if not"""
    def check_etag_header(self):
        # We should never cache the result.
        return False

    def get(self):
        session = self.get_secure_cookie('session')
        if session is None:
            self.set_status(401)
        else:
            self.set_status(200)
        self.set_header('Cache-Control', 'no-cache')
        self.finish()


class Logout(BaseHandler, OIDCClientMixin):
    async def get(self):
        session = self.get_session_cookie()
        if session:
            LOG.info(f"Logging user {session['username']} out")
            self.clear_cookie('session')
            refresh_token = session['refresh_token']
            async with self.get_oidc_client() as oicd_cli:
                try:
                    await oicd_cli.logout(refresh_token)
                except aiohttp.client_exceptions.ClientConnectionError:
                    LOG.warn(
                        'There was a problem logging out (refresh_token expired?).'
                    )
        self.redirect('/')


class MainHandler(BaseHandler):
    async def get(self):
        session = self.get_session_cookie()
        if session is None:
            return self.finish("""
                You are currently not logged in: <a href="/auth/login">Login</a>        
            """)
        else:
            return self.finish(f"""
                You are currently logged in as "{session['username']}":
                <a href="/auth/logout">Logout</a>        
            """)


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/auth/probe", ProbeAuthentication),
            (r'/auth/login', Login),
            (r'/auth/authenticate', Authentication),
            (r'/auth/authorize', Authorization),
            (r'/auth/complete', LoginComplete),
            (r'/auth/logout', Logout),
        ],
        cookie_secret=os.environ['COOKIE_SECRET'],
        debug=True,
        oicd_server=os.environ['OIDC_SERVER'],
        oicd_realm=os.environ['OIDC_REALM'],
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
    )
