export type AuthenticatedUserInfo = {
  email: string | null;
  name: string | null;
};

export type OAuthTokenResponse = {
  access_token?: string;
  token_type?: string;
  scope?: string;
  error?: string;
  error_description?: string;
};

export interface OAuthProvider {
  authUrl: string;
  tokenUrl: string;
  userUrl: string;
  scopes: string[];
  clientId: string;
  clientSecret: string;
  callbackUrl: string;
  mapUserData: (
    apiResponse: any,
    accessToken: string
  ) => Promise<AuthenticatedUserInfo>;
}
