import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { loginApi, registerApi, getMeApi } from '../api/auth';
import { useAuthStore } from '../store/authStore';

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      loginApi(username, password),
    onSuccess: async (data) => {
      // Temporarily set token so getMeApi works
      useAuthStore.setState({ token: data.access_token });
      const user = await getMeApi();
      setAuth(data.access_token, user);
      toast.success('Welcome back!');
      navigate('/');
    },
    onError: () => {
      toast.error('Invalid email or password');
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      registerApi({ email, password }),
    onSuccess: async (data) => {
      useAuthStore.setState({ token: data.access_token });
      const user = await getMeApi();
      setAuth(data.access_token, user);
      toast.success('Account created!');
      navigate('/');
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Registration failed');
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return () => {
    logout();
    toast.success('Logged out');
    navigate('/login');
  };
}
