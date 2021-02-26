try:
    from contextlib import asynccontextmanager
except ImportError:
    # Python 3.6
    from asyncio_extras import async_contextmanager as asynccontextmanager
import datetime
import logging
import os

import aiohttp
from keycloak.aio.realm import KeycloakRealm
import tornado.ioloop
import tornado.web


LOG = logging.getLogger(__name__)


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


class Login(tornado.web.RequestHandler):
    async def get(self):
        # Initiate the OICD flow.
        return self.redirect('/auth/authenticate')


class Authentication(tornado.web.RequestHandler, OIDCClientMixin):
    async def get(self):
        async with self.get_oidc_client() as oidc_cli:
            redirect_uri = f'{self.request.protocol}://{self.request.host}/auth/authorize'
            LOG.info(f'Redirecting to the authorization url. Will return to {redirect_uri}')
            return self.redirect(oidc_cli.authorization_url(redirect_uri=redirect_uri))


class Authorization(tornado.web.RequestHandler, OIDCClientMixin):
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
            seconds_per_day = 60 * 60 * 24

            self.set_secure_cookie(
                'refresh_token', result['refresh_token'],
                expires_days=result['refresh_expires_in'] / seconds_per_day,
            )
            LOG.info(f'Fetching user info')
            user_info = await oidc_cli.userinfo(result['access_token'] or '')

        self.set_cookie('username', user_info['preferred_username'], expires_days=0.1)
        LOG.info(f'User {user_info["preferred_username"]} successfully logged in. Redirecting to complete.')
        return self.redirect(f'/auth/complete')


class LoginComplete(tornado.web.RequestHandler):
    def get(self):
        redirect = self.get_cookie('POST_AUTH_REDIRECT')
        self.clear_cookie('POST_AUTH_REDIRECT')
        if redirect is None:
            LOG.info("Login complete. No redirect specified, redirecting to /")
            self.redirect('/')
        else:
            LOG.info(f"Login complete. Redirecting to {redirect} as was initially requested")
            self.redirect(redirect)


class ProbeAuthentication(tornado.web.RequestHandler):
    """A handler to return 200 if the user is logged in, and 401 if not"""
    def get(self):
        # Our "session" cookie is effectively the refresh_token.
        refresh_token = self.get_secure_cookie('refresh_token')
        self.set_header('Cache-Control', 'no-cache')

        if refresh_token is None:
            self.set_status(401)
        else:
            self.set_status(200)

        username = self.get_cookie('username')
        if username:
            self.set_header('x_forwarded_user', username)

        # Return some unique content to prevent tornado returning a 304
        # (there is probably a better way).
        self.finish(f'{datetime.datetime.now()}')


class Logout(tornado.web.RequestHandler, OIDCClientMixin):
    async def get(self):
        username = self.get_cookie('username')
        if username:
            LOG.info(f"Logging user {username} out")
            self.clear_cookie('username')

        refresh_token = self.get_secure_cookie('refresh_token')
        if refresh_token:
            self.clear_cookie('refresh_token')
            refresh_token = refresh_token.decode()
            async with self.get_oidc_client() as oicd_cli:
                await oicd_cli.logout(refresh_token)

        self.redirect('/')


def make_app():
    return tornado.web.Application(
        [
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
