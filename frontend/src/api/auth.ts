import client from './client';
import type { AuthResponse, User, RegisterPayload } from '../types';

export const loginApi = async (username: string, password: string): Promise<AuthResponse> => {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const { data } = await client.post<AuthResponse>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data;
};

export const registerApi = async (payload: RegisterPayload): Promise<AuthResponse> => {
  const { data } = await client.post<AuthResponse>('/auth/register', payload);
  return data;
};

export const getMeApi = async (): Promise<User> => {
  const { data } = await client.get<User>('/auth/me');
  return data;
};
