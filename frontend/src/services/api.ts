import axios from 'axios';

const getApiBaseUrl = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    // If accessed through Nginx (port 80, 443, or standard domain)
    if (window.location.port === '' || window.location.port === '80' || window.location.port === '443') {
      return ''; // Relative path, seamlessly routed by Nginx
    }
    // If accessed directly on direct port (e.g. 3000)
    if (window.location.port === '3000') {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return '';
  }
  return 'http://admin_api:8000';
};

const API_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// Auth
export const login = (username: string, password: string) =>
  api.post('/api/auth/login', { username, password }).then((r) => r.data);
export const getMe = () => api.get('/api/auth/me').then((r) => r.data);

// Movies
export const getMovies = (params?: Record<string, unknown>) =>
  api.get('/api/movies', { params }).then((r) => r.data);
export const getMovie = (id: number) => api.get(`/api/movies/${id}`).then((r) => r.data);
export const createMovie = (data: unknown) => api.post('/api/movies', data).then((r) => r.data);
export const updateMovie = (id: number, data: unknown) =>
  api.put(`/api/movies/${id}`, data).then((r) => r.data);
export const deleteMovie = (id: number) => api.delete(`/api/movies/${id}`).then((r) => r.data);
export const addVideo = (movieId: number, data: unknown) =>
  api.post(`/api/movies/${movieId}/videos`, data).then((r) => r.data);
export const deleteVideo = (movieId: number, videoId: number) =>
  api.delete(`/api/movies/${movieId}/videos/${videoId}`).then((r) => r.data);

// Serial Episodes
export const getEpisodes = (movieId: number, season?: number) =>
  api.get(`/api/movies/${movieId}/episodes`, { params: { season } }).then((r) => r.data);
export const addEpisode = (movieId: number, data: unknown) =>
  api.post(`/api/movies/${movieId}/episodes`, data).then((r) => r.data);
export const addEpisodesBatch = (movieId: number, data: unknown) =>
  api.post(`/api/movies/${movieId}/episodes/batch`, data).then((r) => r.data);
export const deleteEpisode = (movieId: number, episodeId: number) =>
  api.delete(`/api/movies/${movieId}/episodes/${episodeId}`).then((r) => r.data);

// Users
export const getUsers = (params?: Record<string, unknown>) =>
  api.get('/api/users', { params }).then((r) => r.data);
export const blockUser = (telegramId: number) =>
  api.post(`/api/users/${telegramId}/block`).then((r) => r.data);
export const unblockUser = (telegramId: number) =>
  api.post(`/api/users/${telegramId}/unblock`).then((r) => r.data);

// Channels
export const getChannels = () => api.get('/api/channels').then((r) => r.data);
export const createChannel = (data: unknown) =>
  api.post('/api/channels', data).then((r) => r.data);
export const updateChannel = (id: number, data: unknown) =>
  api.put(`/api/channels/${id}`, data).then((r) => r.data);
export const deleteChannel = (id: number) =>
  api.delete(`/api/channels/${id}`).then((r) => r.data);

// Settings
export const getSettings = () => api.get('/api/settings').then((r) => r.data);
export const updateSettings = (data: unknown) =>
  api.put('/api/settings', data).then((r) => r.data);
export const syncTelegramSettings = () =>
  api.post('/api/settings/sync-telegram').then((r) => r.data);

// Stats
export const getDashboard = () => api.get('/api/stats/dashboard').then((r) => r.data);

// Broadcast
export const sendBroadcast = (data: unknown) =>
  api.post('/api/broadcast', data).then((r) => r.data);
export const getBroadcastStatus = (id: string) =>
  api.get(`/api/broadcast/status/${id}`).then((r) => r.data);

// Admins
export const getAdmins = () => api.get('/api/admins').then((r) => r.data);
export const createAdmin = (data: unknown) =>
  api.post('/api/auth/admins', data).then((r) => r.data);
export const deleteAdmin = (id: number) =>
  api.delete(`/api/admins/${id}`).then((r) => r.data);

// Logs
export const getLogs = (params?: Record<string, unknown>) =>
  api.get('/api/logs', { params }).then((r) => r.data);
