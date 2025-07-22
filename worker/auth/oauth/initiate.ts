import type { OAuthProvider } from './types';

export async function initiateOAuth(
  provider: OAuthProvider,
  currentUrl: string
): Promise<Response> {
  const randomState = crypto.randomUUID();

  // Encode both the random state and the current URL
  const stateData = {
    randomState,
    returnUrl: currentUrl,
  };
  const encodedState = btoa(JSON.stringify(stateData));

  const authUrl = new URL(provider.authUrl);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('client_id', provider.clientId);
  authUrl.searchParams.set('redirect_uri', provider.callbackUrl); // This will be the proxy URL
  authUrl.searchParams.set('scope', provider.scopes.join(' '));
  authUrl.searchParams.set('state', encodedState);

  return new Response(null, {
    status: 302,
    headers: {
      Location: authUrl.toString(),
      'Set-Cookie': `oauth_state=${randomState}; HttpOnly; Secure; SameSite=Lax; Max-Age=600; Path=/`,
    },
  });
}
