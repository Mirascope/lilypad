import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import type { Context } from 'hono';

function isValidPreviewUrl(url: string): boolean {
  try {
    const parsedUrl = new URL(url);
    return (
      parsedUrl.hostname.endsWith(
        '-lilypad-development.mirascope.workers.dev'
      ) || parsedUrl.hostname === 'development.lilypad.mirascope.com'
    );
  } catch {
    return false;
  }
}

export async function handleOAuthProxyCallback(
  c: Context<{ Bindings: Environment; Variables: { db: Database } }>,
  provider: string
): Promise<Response> {
  const url = new URL(c.req.url);
  const code = url.searchParams.get('code');
  const encodedState = url.searchParams.get('state');
  const error = url.searchParams.get('error');
  const errorDescription = url.searchParams.get('error_description');

  // Check for OAuth provider errors first
  if (error) {
    console.error('OAuth error from provider:', error, errorDescription);
    throw new Error(`OAuth Error: ${error} - ${errorDescription || ''}`);
  }

  // Encoded state is required for the OAuth flow
  if (!encodedState) {
    console.error('No state parameter received');
    throw new Error('No state parameter received');
  }

  // Parse the encoded state
  let stateData;
  try {
    stateData = JSON.parse(atob(encodedState));
  } catch (e) {
    console.error('Failed to decode state:', e);
    throw new Error('Invalid state parameter - unable to decode');
  }

  const returnUrl = stateData.returnUrl;
  if (!returnUrl) {
    throw new Error('No return URL found in state');
  }

  if (!isValidPreviewUrl(returnUrl)) {
    console.error('Invalid return URL:', returnUrl);
    throw new Error('Invalid return URL');
  }

  if (!code) {
    console.error('No authorization code received');
    throw new Error('No authorization code received');
  }

  const callbackUrl = new URL(
    `/auth/${provider.toLowerCase()}/callback`,
    returnUrl
  );
  callbackUrl.searchParams.set('code', code);
  callbackUrl.searchParams.set('state', encodedState);

  console.log('Proxying OAuth callback from development to preview:', {
    from: url.toString(),
    to: callbackUrl.toString(),
  });

  return new Response(null, {
    status: 302,
    headers: {
      Location: callbackUrl.toString(),
      'Set-Cookie': `oauth_state=${stateData.randomState}; HttpOnly; Secure; SameSite=Lax; Max-Age=600; Path=/`,
    },
  });
}
