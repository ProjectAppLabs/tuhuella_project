import { describe, it, expect, beforeEach } from '@jest/globals';
import { act } from '@testing-library/react';

import { useAuthStore } from '../authStore';
import { api } from '../../services/http';
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '../../services/tokens';

jest.mock('../../services/http', () => ({
  api: {
    post: jest.fn(),
    get: jest.fn(),
    patch: jest.fn(),
  },
}));

jest.mock('../../services/tokens', () => ({
  getAccessToken: jest.fn(),
  getRefreshToken: jest.fn(),
  setTokens: jest.fn(),
  clearTokens: jest.fn(),
}));

const mockApi = api as jest.Mocked<typeof api> & { get: jest.Mock };
const mockGetAccessToken = getAccessToken as jest.Mock;
const mockGetRefreshToken = getRefreshToken as jest.Mock;
const mockSetTokens = setTokens as jest.Mock;
const mockClearTokens = clearTokens as jest.Mock;

const resetAuthState = () => {
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
    isAuthReady: false,
    profileStats: null,
    activity: [],
    profileLoading: false,
  });
};

describe('authStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    resetAuthState();
    mockGetAccessToken.mockReturnValue(null);
    mockGetRefreshToken.mockReturnValue(null);
  });

  it('syncs tokens from cookies', () => {
    mockGetAccessToken.mockReturnValue('access');
    mockGetRefreshToken.mockReturnValue('refresh');
    mockApi.get.mockResolvedValue({ data: { user: null } });

    act(() => {
      useAuthStore.getState().syncFromCookies();
    });

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe('access');
    expect(state.refreshToken).toBe('refresh');
    expect(state.isAuthenticated).toBe(true);
  });

  it('signs in successfully', async () => {
    mockGetAccessToken.mockReturnValue('access');
    mockGetRefreshToken.mockReturnValue('refresh');
    mockApi.post.mockResolvedValueOnce({
      data: {
        access: 'access',
        refresh: 'refresh',
        user: {
          id: 1,
          email: 'user@example.com',
          first_name: 'Test',
          last_name: 'User',
          role: 'customer',
          is_staff: false,
        },
      },
    });

    await act(async () => {
      await useAuthStore.getState().signIn({ email: 'user@example.com', password: 'password' });
    });

    expect(mockSetTokens).toHaveBeenCalledWith({ access: 'access', refresh: 'refresh' });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().user?.email).toBe('user@example.com');
  });

  it('throws when sign in response is missing tokens', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { access: null, refresh: null } });

    await expect(useAuthStore.getState().signIn({ email: 'user@example.com', password: 'password' })).rejects.toThrow(
      'Invalid token response'
    );
  });

  it('signs up successfully', async () => {
    mockGetAccessToken.mockReturnValue('access');
    mockGetRefreshToken.mockReturnValue('refresh');
    mockApi.post.mockResolvedValueOnce({
      data: {
        access: 'access',
        refresh: 'refresh',
        user: {
          id: 2,
          email: 'new@example.com',
          first_name: 'New',
          last_name: 'User',
          role: 'customer',
          is_staff: false,
        },
      },
    });

    await act(async () => {
      await useAuthStore.getState().signUp({ email: 'new@example.com', password: 'password' });
    });

    expect(mockSetTokens).toHaveBeenCalledWith({ access: 'access', refresh: 'refresh' });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('throws when sign up response is missing tokens', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { access: null, refresh: null } });

    await expect(
      useAuthStore.getState().signUp({ email: 'new@example.com', password: 'password' })
    ).rejects.toThrow('Invalid token response');
  });

  it('logs in with google credentials', async () => {
    mockGetAccessToken.mockReturnValue('access');
    mockGetRefreshToken.mockReturnValue('refresh');
    mockApi.post.mockResolvedValueOnce({
      data: {
        access: 'access',
        refresh: 'refresh',
        user: {
          id: 3,
          email: 'google@example.com',
          first_name: 'Google',
          last_name: 'User',
          role: 'customer',
          is_staff: false,
        },
      },
    });

    await act(async () => {
      await useAuthStore.getState().googleLogin({ credential: 'token', email: 'google@example.com' });
    });

    expect(mockSetTokens).toHaveBeenCalledWith({ access: 'access', refresh: 'refresh' });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('throws when google login response is missing tokens', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { access: null, refresh: null } });

    await expect(useAuthStore.getState().googleLogin({ credential: 'token' })).rejects.toThrow('Invalid token response');
  });

  it('signs out and clears tokens', () => {
    useAuthStore.setState({ isAuthenticated: true, accessToken: 'access', refreshToken: 'refresh' });

    act(() => {
      useAuthStore.getState().signOut();
    });

    expect(mockClearTokens).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  it('sends a password reset code', async () => {
    mockApi.post.mockResolvedValueOnce({ data: {} });

    await act(async () => {
      await useAuthStore.getState().sendPasswordResetCode('user@example.com');
    });

    expect(mockApi.post).toHaveBeenCalledWith('/auth/send_passcode/', { email: 'user@example.com', locale: undefined });
  });

  it('resets password', async () => {
    mockApi.post.mockResolvedValueOnce({ data: {} });

    await act(async () => {
      await useAuthStore
        .getState()
        .resetPassword({ email: 'user@example.com', code: '123456', new_password: 'password123' });
    });

    expect(mockApi.post).toHaveBeenCalledWith('/auth/verify_passcode_and_reset_password/', {
      email: 'user@example.com',
      code: '123456',
      new_password: 'password123',
    });
  });

  it('fetchMe sets user on success', async () => {
    const mockUser = { id: 1, email: 'test@example.com', first_name: 'Test', last_name: 'User', role: 'adopter' };
    mockApi.get.mockResolvedValueOnce({ data: { user: mockUser } });

    await act(async () => {
      await useAuthStore.getState().fetchMe();
    });

    expect(useAuthStore.getState().user).toEqual(mockUser);
  });

  it('fetchMe signs out when credentials are rejected', async () => {
    useAuthStore.setState({ isAuthenticated: true, accessToken: 'token' });
    mockApi.get.mockRejectedValueOnce({ response: { status: 401 } });

    await act(async () => {
      await useAuthStore.getState().fetchMe();
    });

    expect(mockClearTokens).toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it.each([
    ['503', { response: { status: 503 } }],
    ['network failure', new Error('Network Error')],
    ['timeout', Object.assign(new Error('timeout'), { code: 'ECONNABORTED' })],
  ])('fetchMe preserves the session after %s', async (_scenario, validationError) => {
    useAuthStore.setState({ isAuthenticated: true, accessToken: 'access', refreshToken: 'refresh' });
    const user = {
      id: 1, email: 'test@example.com', first_name: 'Test', last_name: 'User',
      phone: '', city: '', role: 'adopter' as const, is_staff: false, date_joined: '2026-10-08',
    };
    useAuthStore.setState({ user });
    mockApi.get.mockRejectedValueOnce(validationError);

    await act(async () => {
      await useAuthStore.getState().fetchMe();
    });

    expect(useAuthStore.getState()).toMatchObject({
      isAuthenticated: true, accessToken: 'access', refreshToken: 'refresh', user,
    });
    expect(mockClearTokens).not.toHaveBeenCalled();
    expect(mockApi.get).toHaveBeenCalledTimes(1);
  });

  it('fetchMe recovers user details after a transient validation failure', async () => {
    useAuthStore.setState({ isAuthenticated: true, accessToken: 'access', refreshToken: 'refresh' });
    const mockUser = { id: 1, email: 'test@example.com', role: 'adopter' };
    mockApi.get.mockRejectedValueOnce({ response: { status: 503 } });
    mockApi.get.mockResolvedValueOnce({ data: { user: mockUser } });

    await act(async () => {
      await useAuthStore.getState().fetchMe();
      await useAuthStore.getState().fetchMe();
    });

    expect(useAuthStore.getState().user).toEqual(mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(mockClearTokens).not.toHaveBeenCalled();
  });

  it('fetchProfileStats sets stats on success', async () => {
    const stats = { favorites_count: 5, applications_count: 2 };
    mockApi.get.mockResolvedValueOnce({ data: stats });

    await act(async () => {
      await useAuthStore.getState().fetchProfileStats();
    });

    expect(useAuthStore.getState().profileStats).toEqual(stats);
    expect(useAuthStore.getState().profileLoading).toBe(false);
  });

  it('fetchProfileStats handles error silently', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('fail'));

    await act(async () => {
      await useAuthStore.getState().fetchProfileStats();
    });

    expect(useAuthStore.getState().profileStats).toBeNull();
    expect(useAuthStore.getState().profileLoading).toBe(false);
  });

  it('fetchActivity sets activity on success', async () => {
    const events = [{ id: 1, type: 'login', created_at: '2026-01-01' }];
    mockApi.get.mockResolvedValueOnce({ data: events });

    await act(async () => {
      await useAuthStore.getState().fetchActivity();
    });

    expect(useAuthStore.getState().activity).toEqual(events);
  });

  it('fetchActivity handles error silently', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('fail'));

    await act(async () => {
      await useAuthStore.getState().fetchActivity();
    });

    expect(useAuthStore.getState().activity).toEqual([]);
  });

  it('updateProfile updates user on success', async () => {
    const updatedUser = { id: 1, email: 'test@example.com', first_name: 'Updated', last_name: 'User', role: 'adopter' };
    mockApi.patch.mockResolvedValueOnce({ data: updatedUser });

    await act(async () => {
      await useAuthStore.getState().updateProfile({ first_name: 'Updated' });
    });

    expect(useAuthStore.getState().user).toEqual(updatedUser);
  });
});
