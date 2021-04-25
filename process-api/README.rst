=======================
taitokartta
=======================

Development
===========

.. code:: bash

   $ make shell
   [nix-shell]$ make watch

Or

.. code:: bash

   $ make nix-watch


OIDC environment
================

Docker Compose -configuration brings up Keycloak at http://localhost:8080 with

.. code:: bash

   $ docker-compose up

It has the following OIDC configuration available::

    APP_AUTHORITY = "http://localhost:8080/auth/realms/taitokartta"
    APP_REDIRECT_URI = "http://localhost:3000/signinCallback"
    CLIENT_ID = "taitokartta"

The client is configured as public client with authorization flow, which is supported by ``oidc-client`` JavaScript library with the following configuration, for example::

    const AUTHORITY = "http://localhost:8080/auth/realms/taitokartta"
    const CLIENT_ID = "taitokartta"
    const REDIRECT_URI = "http://localhost:3000/signinCallback"
    const POST_LOGOUT_REDIRECT_URI = "http://localhost:3000/signoutCallback"

    const clientSettings = {
      authority: AUTHORITY,
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      post_logout_redirect_uri: POST_LOGOUT_REDIRECT_URI,
      response_type: "code",
      scope: "openid email profile",
      filterProtocolClaims: true,
      loadUserInfo: true,
      automaticSilentRenew: true,
      accessTokenExpiringNotificationTime: 30,
    };

The following ``username:password`` combinations are preconfigured::

    johndoe:johndoe
    janedoe:janedoe
