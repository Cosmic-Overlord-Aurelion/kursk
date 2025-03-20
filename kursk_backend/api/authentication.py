from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication
from rest_framework import exceptions

class CustomTokenAuthentication(BaseTokenAuthentication):
    def authenticate(self, request):
        print("DEBUG: CustomTokenAuthentication called")
        print("DEBUG: Request headers in TokenAuthentication:", dict(request.headers))
        auth = request.headers.get('Authorization')
        if not auth:
            print("DEBUG: No Authorization header found")
            return None

        if not auth.startswith('Token '):
            print("DEBUG: Invalid Authorization header format:", auth)
            raise exceptions.AuthenticationFailed('Invalid token header. Must start with "Token".')

        token = auth[len('Token '):].strip()
        if not token:
            print("DEBUG: Token is empty")
            raise exceptions.AuthenticationFailed('Invalid token header. Token string is empty.')

        print("DEBUG: Extracted token:", token)
        return self.authenticate_credentials(token)