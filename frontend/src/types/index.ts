export interface Movie {
  id: number;
  code: string;
  content_type?: 'movie' | 'serial';
  title: string;
  original_title?: string;
  poster_file_id?: string;
  description?: string;
  year?: number;
  country?: string;
  duration_minutes?: number;
  total_seasons?: number;
  total_episodes?: number;
  imdb_rating?: number;
  status: 'published' | 'hidden' | 'draft';
  views_count: number;
  created_at: string;
  updated_at: string;
  genres: string[];
  videos: Video[];
  episodes?: Episode[];
}

export interface Episode {
  id: number;
  movie_id: number;
  season_number: number;
  episode_number: number;
  title?: string;
  telegram_file_id: string;
  quality: string;
  duration_seconds: number;
  file_size_bytes: number;
  views_count: number;
  created_at: string;
}

export interface Video {
  id: number;
  quality: '360p' | '480p' | '720p' | '1080p' | '4K';
  telegram_file_id: string;
  duration_seconds: number;
  file_size_bytes: number;
}

export interface User {
  id: number;
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  is_blocked: boolean;
  joined_at: string;
  last_activity: string;
}

export interface Channel {
  id: number;
  channel_id: number;
  username: string;
  title: string;
  is_active: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  new_users_today: number;
  total_movies: number;
  total_views: number;
  searches_today: number;
  top_movies: { id: number; title: string; views_count: number }[];
  not_found_searches: { query: string; count: number }[];
  popular_searches: { query: string; count: number }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface Admin {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  last_login?: string;
}

export interface Log {
  id: number;
  action: string;
  entity_type?: string;
  entity_id?: number;
  admin_id?: number;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface BroadcastStatus {
  broadcast_id: string;
  total: number;
  sent: number;
  failed: number;
  done: boolean;
}

export interface Settings {
  [key: string]: string;
}
