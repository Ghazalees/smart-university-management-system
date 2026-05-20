export interface MeResponse {
  success: boolean;
  data: {
    id: number;
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    role: string;
  };
}

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  role: string | null;
}

export interface CredentialsPayload {
  user: User;
  accessToken: string;
  role: string;
}
