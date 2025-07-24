import { createOrUpdateUser, createSession } from '@/db/operations';
import { DEFAULT_SESSION_DURATION } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import type { Context } from 'hono';
import type {
  AuthenticatedUserInfo,
  OAuthProvider,
  OAuthTokenResponse,
} from './types';

async function processAuthenticatedUser(
  c: Context<{ Bindings: Environment; Variables: { db: Database } }>,
  userInfo: AuthenticatedUserInfo,
  returnUrl?: string
) {
  const siteUrl = returnUrl || c.env.SITE_URL;
  try {
    if (!userInfo.email) {
      throw new Error('Email is required to process an authenticated user');
    }
    const db = c.get('db');
    const user = await createOrUpdateUser(db, {
      email: userInfo.email,
      name: userInfo.name,
    });

    if (!user) {
      throw new Error('Failed to create/update user');
    }

    const sessionId = await createSession(db, user.id);

    if (!sessionId) {
      throw new Error('Failed to create session');
    }

    const redirectUrl = new URL(siteUrl);
    redirectUrl.searchParams.set('success', 'true');
    redirectUrl.searchParams.set(
      'user',
      encodeURIComponent(
        JSON.stringify({
          id: user.id,
          email: user.email,
          name: user.name,
        })
      )
    );

    const sessionCookie = [
      `session=${sessionId}`,
      'HttpOnly',
      'Secure',
      'SameSite=Lax',
      `Max-Age=${DEFAULT_SESSION_DURATION}`,
      'Path=/',
    ].join('; ');

    return new Response(null, {
      status: 302,
      headers: {
        Location: redirectUrl.toString(),
        'Set-Cookie': sessionCookie,
      },
    });
  } catch (error) {
    console.error('Error processing authentication:', error);

    const errorUrl = new URL(siteUrl);
    errorUrl.searchParams.set('error', 'authentication_failed');

    return new Response(null, {
      status: 302,
      headers: {
        Location: errorUrl.toString(),
      },
    });
  }
}

// Generic OAuth callback handling
export async function handleOAuthCallback(
  c: Context<{ Bindings: Environment; Variables: { db: Database } }>,
  provider: OAuthProvider
): Promise<Response> {
  const url = new URL(c.req.url);
  const code = url.searchParams.get('code');
  const encodedState = url.searchParams.get('state');

  // Check if we got an error from the provider
  const error = url.searchParams.get('error');
  if (error) {
    console.error('OAuth error:', error);
    throw new Error(`OAuth Error: ${error}`);
  }

  // Check if we got the required code
  if (!code) {
    console.error('No authorization code received');
    throw new Error('No authorization code received');
  }

  if (!encodedState) {
    console.error('No state received');
    throw new Error('No state received');
  }
  let stateData;
  try {
    stateData = JSON.parse(atob(encodedState));
  } catch (e) {
    throw new Error(`Failed to decode state: ${e}`);
  }

  const { randomState, returnUrl } = stateData;

  // Verify the state parameter (basic security check)
  const cookies = c.req.header('Cookie');
  const storedState = cookies
    ?.split('; ')
    .find((row) => row.startsWith('oauth_state='))
    ?.split('=')[1];

  if (storedState !== randomState) {
    throw new Error('Invalid state parameter');
  }

  // Step 1: Exchange code for access token
  const tokenResponse = await fetch(provider.tokenUrl, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: provider.clientId,
      client_secret: provider.clientSecret,
      code: code,
      redirect_uri: provider.callbackUrl,
    }),
  });

  const tokenData = (await tokenResponse.json()) as OAuthTokenResponse;

  if (tokenData.error) {
    console.error('Token exchange failed:', tokenData.error);
    throw new Error(`Token exchange failed: ${tokenData.error}`);
  }

  if (!tokenData.access_token) {
    console.error('No access token received');
    throw new Error('No access token received');
  }

  // Step 2: Use access token to get user information
  const userResponse = await fetch(provider.userUrl, {
    headers: {
      Authorization: `Bearer ${tokenData.access_token}`,
      Accept: 'application/json',
      'User-Agent': 'Mirascope/0.1',
    },
  });

  if (!userResponse.ok) {
    console.error(
      'Failed to fetch user data:',
      userResponse.status,
      userResponse.statusText
    );
    throw new Error('Failed to fetch user data');
  }

  const userData = await userResponse.json();
  const userInfo = await provider.mapUserData(userData, tokenData.access_token);
  const response = await processAuthenticatedUser(c, userInfo, returnUrl);

  const deleteStateCookieHeader = [
    'oauth_state=;',
    'Expires=Thu, 01 Jan 1970 00:00:00 GMT', // Force immediate expiration
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
    'Path=/',
  ].join('; ');

  response.headers.append('Set-Cookie', deleteStateCookieHeader);
  return response;
}
