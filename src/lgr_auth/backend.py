#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import logging

from django.conf import settings
from django.contrib.auth.backends import UserModel, ModelBackend
from okta_jwt_verifier import BaseJWTVerifier

logger = logging.getLogger(__name__)


async def check_id_token(jwt_verifier, id_token):
    await jwt_verifier.verify_id_token(id_token, nonce=settings.ICANN_AUTH_NONCE)


async def get_user_info(jwt_verifier, access_token, id_token):
    headers, claims, signing_input, signature = jwt_verifier.parse_token(access_token)
    # verify the access token signature
    okta_jwk = await jwt_verifier.get_jwk(headers['kid'])
    jwt_verifier.verify_signature(access_token, okta_jwk)

    data = {
        'email': claims.get('email'),
        'first_name': claims.get('given_name'),
        'last_name': claims.get('family_name'),
    }
    headers, claims, signing_input, signature = jwt_verifier.parse_token(id_token)
    data['username'] = claims['preferred_username']

    return data


class JWTBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, request, **kwargs):
        body = request.body.decode('utf-8').split('&')
        params = {}
        for b in body:
            k, v = b.split('=', 1)
            params[k] = v
        id_token = params.get('id_token')
        access_token = params.get('access_token')

        if not id_token or not access_token:
            logger.warning('No ID token nor access token')
            return
        jwt_verifier = BaseJWTVerifier(issuer=settings.ICANN_AUTH_ISSUER, client_id=settings.ICANN_AUTH_CLIENT_ID)
        try:
            asyncio.run(check_id_token(jwt_verifier, id_token))
            claims = asyncio.run(get_user_info(jwt_verifier, access_token, id_token))
            return self._authenticate_from_claims(claims)
        except Exception as e:
            logger.exception('Failed to log-in', e)
            return

    def _authenticate_from_claims(self, claims):
        first_name = claims.get('first_name')
        last_name = claims.get('last_name')
        email = claims.get('email')
        username = claims.get('username')
        try:
            user = UserModel._default_manager.get(icann_username__iexact=username)
        except UserModel.DoesNotExist:
            try:
                # try to get the user by its email if ICANN account is not linked yet
                user = UserModel._default_manager.get_by_natural_key(email)
            except UserModel.DoesNotExist:
                # create the user in the database
                user = UserModel.objects.create_user(email, first_name=first_name, last_name=last_name,
                                                     icann_username=username)
        else:
            if user.first_name != first_name or user.last_name != last_name or email != user.email:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save(update_fields=['first_name', 'last_name', 'email'])

        user._lgr_state = claims.get('state')  # keep state in user in case we want to do different processing
        if self.user_can_authenticate(user):
            return user
        else:
            logger.warning('User cannot authenticate')
            return
