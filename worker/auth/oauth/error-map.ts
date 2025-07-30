import { OAuthError } from './oauth-error';

export function mapOAuthError(err: unknown): string {
  if (err instanceof OAuthError) {
    return `/?error=${encodeURIComponent(err.code)}`;
  }

  if (err instanceof Error) {
    // Map specific error messages to appropriate error codes
    if (err.message.includes('OAuth Error:')) {
      const errorCode = err.message.replace('OAuth Error: ', '');
      return `/?error=${encodeURIComponent(errorCode)}`;
    }

    if (err.message === 'No authorization code received') {
      return '/?error=missing_code';
    }

    if (err.message.includes('Invalid state parameter')) {
      return '/?error=invalid_state';
    }
  }

  // Fallback for unexpected errors
  return '/?error=server_error';
}
