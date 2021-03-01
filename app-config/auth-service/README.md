# auth-service

A simple auth service using OIDC which can be interrogated by NGINX.


To use, set the following environment variables:

 * COOKIE_SECRET
 * OIDC_SERVER
 * OIDC_REALM
 * CLIENT_ID
 * CLIENT_SECRET

Then ``python -m auth_service``.

Once running, visit http://localhost:8080/auth/probe to find out if you are
already authenticated. Since you just started the app, you won't be authenticated,
so a 401 will be returned. Now go and visit http://localhost:8080/auth/login, which
will take you through the OIDC code authorization flow. Once complete you will eventually
be redirected to http://localhost:8080 and be told that you are now logged in.
Now go back to http://localhost:8080/auth/probe to observe that your now authenticated.

To logout, hit http://localhost:8080/auth/logout. You'll be redirected to
http://localhost:8080 with no login setup. Confirm this by again visiting
http://localhost:8080/auth/probe and getting a 401 again.

At this point, you may be wondering why would you want so many 401 errors.
The idea of this service is to be able to use
[nginx's ``ngx_http_auth_request_module``](
http://nginx.org/en/docs/http/ngx_http_auth_request_module.html).
A nice tutorial of using it inspired the creation of this package and may be
interesting to the curious reader
(https://redbyte.eu/en/blog/using-the-nginx-auth-request-module/).

## Integrating into NGINX

As mentioned, typically nginx has the [``ngx_http_auth_request_module``](
http://nginx.org/en/docs/http/ngx_http_auth_request_module.html) built-in, and so
we want to be able to profit from its ability to only allow authorized access to
certain specified locations.

In our nginx config we declare ``auth_request /auth/probe;`` for all
locations that should be authenticated. This endpoint (as you've already seen)
must either return a 200 or a 401 (and no other status!) depending on whether the
user is auth-ed or not. If we are authorized then nginx will redirect to the location,
otherwise we trigger a specialised 401 error with ``error_page 401 = @error401;`` which
essentially has a definition of:

```
    location @error401 {
        return 302 /auth/login;
    }
```

In English: if the page is not authorized, redirect the browser to the login page.
