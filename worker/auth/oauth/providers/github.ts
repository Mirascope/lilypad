import type { Environment } from '@/worker/environment';
import type { AuthenticatedUserInfo, OAuthProvider } from '../types';

type GitHubUser = {
  id: number;
  login: string;
  name: string | null;
  email: string | null;
  avatar_url: string;
  bio: string | null;
  created_at: string;
  updated_at: string;
};

type GitHubEmail = {
  email: string;
  primary: boolean;
  verified: boolean;
  visibility: string | null;
};

async function mapGitHubUserData(
  apiResponse: GitHubUser,
  accessToken: string
): Promise<AuthenticatedUserInfo> {
  let userEmail = apiResponse.email;

  // If email is not in profile, fetch from emails endpoint
  if (!userEmail) {
    const emailResponse = await fetch('https://api.github.com/user/emails', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'MyApp/1.0',
      },
    });

    if (emailResponse.ok) {
      const emailData = (await emailResponse.json()) as GitHubEmail[];
      const primaryEmail = emailData.find((email) => email.primary);
      userEmail = primaryEmail ? primaryEmail.email : null;
    }
  }

  return {
    email: userEmail,
    name: apiResponse.name,
  };
}

export function createGitHubProvider(env: Environment): OAuthProvider {
  return {
    authUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl: 'https://github.com/login/oauth/access_token',
    userUrl: 'https://api.github.com/user',
    scopes: ['user:email'],
    clientId: env.GITHUB_CLIENT_ID,
    clientSecret: env.GITHUB_CLIENT_SECRET,
    callbackUrl: env.GITHUB_CALLBACK_URL,
    mapUserData: mapGitHubUserData,
  };
}
