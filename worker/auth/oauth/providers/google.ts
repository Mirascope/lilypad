import type { Environment } from '@/worker/environment';
import type { AuthenticatedUserInfo, OAuthProvider } from '../types';

type GoogleUser = {
  id: string;
  email: string;
  verified_email: boolean;
  name: string;
  given_name: string;
  family_name: string;
  picture: string;
  locale: string;
};

async function mapGoogleUserData(
  apiResponse: GoogleUser,
  _accessToken: string
): Promise<AuthenticatedUserInfo> {
  return {
    email: apiResponse.email,
    name: apiResponse.name,
  };
}

export function createGoogleProvider(env: Environment): OAuthProvider {
  return {
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    userUrl: 'https://www.googleapis.com/oauth2/v1/userinfo',
    scopes: ['openid', 'email', 'profile'],
    clientId: env.GOOGLE_CLIENT_ID,
    clientSecret: env.GOOGLE_CLIENT_SECRET,
    callbackUrl: env.GOOGLE_CALLBACK_URL,
    mapUserData: mapGoogleUserData,
  };
}
