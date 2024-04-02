from typing import Annotated, Iterable, Optional
from dataclasses import dataclass
from functools import cached_property

import jwt
from fastapi import FastAPI, HTTPException, Security, security, status


@dataclass
class KeycloakAuth:
    realm: str
    host: str
    client_id: str
    internal_host: Optional[str] = None

    required_audience: Optional[str | Iterable[str]] = None

    def _build_url(self, host: str):
        return f"{host}/realms/{self.realm}/protocol/openid-connect"

    @property
    def user_validator(
        self,
    ):
        def valid_user_token(
            token_str: Annotated[str, Security(self.scheme)],
            required_scopes: security.SecurityScopes,
        ):
            # Parse & validate token
            try:
                token = jwt.decode(
                    token_str,
                    self.jwks_client.get_signing_key_from_jwt(token_str).key,
                    algorithms=["RS256"],
                    audience=self.required_audience,
                )
            except jwt.exceptions.DecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e

            # Validate scopes (if required)
            for scope in required_scopes.scopes:
                if scope not in token["scope"]:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not enough permissions",
                        headers={
                            "WWW-Authenticate": f'Bearer scope="{required_scopes.scope_str}"'
                        },
                    )

            return token

        return valid_user_token

    @property
    def internal_keycloak_api(self):
        return self._build_url(self.internal_host or self.host)

    @property
    def keycloak_api(self):
        return self._build_url(self.host)

    @property
    def scheme(self):
        return security.OAuth2AuthorizationCodeBearer(
            authorizationUrl=f"{self.keycloak_api}/auth",
            tokenUrl=f"{self.keycloak_api}/token",
            scopes={},
        )

    @cached_property
    def jwks_client(self):
        return jwt.PyJWKClient(f"{self.internal_keycloak_api}/certs")
