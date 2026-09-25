'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getMovie,
  updateMovie,
  addVideo,
  deleteVideo,
  addEpisode,
  addEpisodesBatch,
  deleteEpisode,
} from '@/services/api';
import { useRouter, useParams } from 'next/navigation';
import {
  Plus,
  Trash2,
  Film,
  ArrowLeft,
  Video,
  Save,
  Image as ImageIcon,
  Tv,
  Layers,
  Sparkles,
  Copy,
  Check,
  List,
} from 'lucide-react';
import Link from 'next/link';
import type { Episode } from '@/types';

const QUALITIES = ['360p', '480p', '720p', '1080p', '4K'];

export default function EditMoviePage() {
  const router = useRouter();
  const params = useParams();
  const movieId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  const { data: movie, isLoading } = useQuery({
    queryKey: ['movie', movieId],
    queryFn: () => getMovie(movieId),
  });

  const [form, setForm] = useState({
    title: '',
    content_type: 'movie',
    original_title: '',
    poster_file_id: '',
    description: '',
    year: '',
    country: '',
    duration_minutes: '',
    total_seasons: '',
    total_episodes: '',
    imdb_rating: '',
    status: 'published',
    genres: '',
  });

  // Movie quality videos state
  const [newQuality, setNewQuality] = useState('720p');
  const [newFileId, setNewFileId] = useState('');
  const [error, setError] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Serial episodes UI state
  const [episodeMode, setEpisodeMode] = useState<'single' | 'batch' | 'list'>('list');
  const [seasonFilter, setSeasonFilter] = useState<number | 'all'>('all');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Single episode form
  const [singleSeason, setSingleSeason] = useState<number>(1);
  const [singleEpNum, setSingleEpNum] = useState<number>(1);
  const [singleTitle, setSingleTitle] = useState<string>('');
  const [singleQuality, setSingleQuality] = useState<string>('720p');
  const [singleFileId, setSingleFileId] = useState<string>('');
  const [singleDuration, setSingleDuration] = useState<string>('');

  // Batch episode form
  const [batchSeason, setBatchSeason] = useState<number>(1);
  const [batchStartEp, setBatchStartEp] = useState<number>(1);
  const [batchQuality, setBatchQuality] = useState<string>('720p');
  const [batchFileIds, setBatchFileIds] = useState<string>('');
  const [batchSuccessMsg, setBatchSuccessMsg] = useState<string>('');

  useEffect(() => {
    if (movie) {
      setForm({
        title: movie.title || '',
        content_type: movie.content_type || 'movie',
        original_title: movie.original_title || '',
        poster_file_id: movie.poster_file_id || '',
        description: movie.description || '',
        year: movie.year ? String(movie.year) : '',
        country: movie.country || '',
        duration_minutes: movie.duration_minutes ? String(movie.duration_minutes) : '',
        total_seasons: movie.total_seasons ? String(movie.total_seasons) : '',
        total_episodes: movie.total_episodes ? String(movie.total_episodes) : '',
        imdb_rating: movie.imdb_rating ? String(movie.imdb_rating) : '',
        status: movie.status || 'published',
        genres: (movie.genres || []).join(', '),
      });
    }
  }, [movie]);

  // Compute next available episode numbers when season changes or episodes load
  useEffect(() => {
    if (movie?.episodes) {
      const seasonEps = movie.episodes.filter((e: Episode) => e.season_number === singleSeason);
      const maxEp = seasonEps.reduce((m: number, e: Episode) => Math.max(m, e.episode_number), 0);
      setSingleEpNum(maxEp + 1);
      setSingleTitle(`${maxEp + 1}-qism`);
    }
  }, [singleSeason, movie?.episodes]);

  useEffect(() => {
    if (movie?.episodes) {
      const seasonEps = movie.episodes.filter((e: Episode) => e.season_number === batchSeason);
      const maxEp = seasonEps.reduce((m: number, e: Episode) => Math.max(m, e.episode_number), 0);
      setBatchStartEp(maxEp + 1);
    }
  }, [batchSeason, movie?.episodes]);

  const updateMutation = useMutation({
    mutationFn: (data: any) => updateMovie(movieId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
      queryClient.invalidateQueries({ queryKey: ['movies'] });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    },
    onError: (e: any) => setError(e.response?.data?.detail || "Saqlashda xatolik yuz berdi"),
  });

  const addVideoMut = useMutation({
    mutationFn: (data: any) => addVideo(movieId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
      setNewFileId('');
    },
  });

  const deleteVideoMut = useMutation({
    mutationFn: (videoId: number) => deleteVideo(movieId, videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
    },
  });

  // Episode mutations
  const addEpisodeMut = useMutation({
    mutationFn: (data: any) => addEpisode(movieId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
      setSingleFileId('');
      setSingleDuration('');
      setEpisodeMode('list');
    },
    onError: (e: any) => alert(e.response?.data?.detail || "Qismni qo'shishda xatolik"),
  });

  const addBatchEpisodeMut = useMutation({
    mutationFn: (data: any) => addEpisodesBatch(movieId, data),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
      setBatchFileIds('');
      setBatchSuccessMsg(`✓ ${data.length} ta qism muvaffaqiyatli yuklandi!`);
      setTimeout(() => setBatchSuccessMsg(''), 4000);
      setEpisodeMode('list');
    },
    onError: (e: any) => alert(e.response?.data?.detail || "Ommaviy yuklashda xatolik"),
  });

  const deleteEpisodeMut = useMutation({
    mutationFn: (episodeId: number) => deleteEpisode(movieId, episodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movie', movieId] });
    },
    onError: (e: any) => alert(e.response?.data?.detail || "Qismni o'chirishda xatolik"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const data = {
      title: form.title.trim(),
      content_type: form.content_type,
      original_title: form.original_title.trim() || undefined,
      poster_file_id: form.poster_file_id.trim() || undefined,
      description: form.description.trim() || undefined,
      year: form.year ? parseInt(form.year) : undefined,
      country: form.country.trim() || undefined,
      duration_minutes: form.duration_minutes ? parseInt(form.duration_minutes) : undefined,
      total_seasons: form.total_seasons ? parseInt(form.total_seasons) : undefined,
      total_episodes: form.total_episodes ? parseInt(form.total_episodes) : undefined,
      imdb_rating: form.imdb_rating ? parseFloat(form.imdb_rating) : undefined,
      status: form.status,
      genres: form.genres
        ? form.genres
            .split(',')
            .map((g) => g.trim())
            .filter(Boolean)
        : [],
    };
    updateMutation.mutate(data);
  };

  const handleAddVideo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFileId.trim()) return;
    addVideoMut.mutate({
      quality: newQuality,
      telegram_file_id: newFileId.trim(),
    });
  };

  const handleSingleEpisodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleFileId.trim()) {
      alert("Telegram video file_id kiritilishi shart!");
      return;
    }
    addEpisodeMut.mutate({
      season_number: Number(singleSeason),
      episode_number: Number(singleEpNum),
      title: singleTitle.trim() || `${singleEpNum}-qism`,
      telegram_file_id: singleFileId.trim(),
      quality: singleQuality,
      duration_seconds: singleDuration ? parseInt(singleDuration) * 60 : 0,
    });
  };

  const handleBatchEpisodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const lines = batchFileIds
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) {
      alert("Kamida bitta Telegram file_id kiritilishi kerak!");
      return;
    }

    addBatchEpisodeMut.mutate({
      season_number: Number(batchSeason),
      start_episode_number: Number(batchStartEp),
      quality: batchQuality,
      file_ids: lines,
    });
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Distinct seasons in episodes
  const distinctSeasons = useMemo(() => {
    if (!movie?.episodes) return [];
    const seasons = Array.from(new Set(movie.episodes.map((e: Episode) => e.season_number))) as number[];
    return seasons.sort((a, b) => a - b);
  }, [movie?.episodes]);

  // Filtered episodes
  const filteredEpisodes = useMemo(() => {
    if (!movie?.episodes) return [];
    let list = [...movie.episodes];
    if (seasonFilter !== 'all') {
      list = list.filter((e: Episode) => e.season_number === seasonFilter);
    }
    return list.sort((a, b) => {
      if (a.season_number !== b.season_number) return a.season_number - b.season_number;
      return a.episode_number - b.episode_number;
    });
  }, [movie?.episodes, seasonFilter]);

  const batchCount = useMemo(() => {
    return batchFileIds
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean).length;
  }, [batchFileIds]);

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="h-64 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </AdminLayout>
    );
  }

  const isSerial = form.content_type === 'serial';

  return (
    <AdminLayout>
      <div className="max-w-4xl space-y-6 pb-16">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/movies"
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {isSerial ? 'Serialni' : 'Kinoni'} tahrirlash
                </h1>
                <code className="text-sm font-mono text-indigo-500 font-semibold bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded">
                  #{movie?.code}
                </code>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    isSerial
                      ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                  }`}
                >
                  {isSerial ? '📺 Serial' : '🎬 Kino'}
                </span>
              </div>
              <p className="text-gray-500 text-sm mt-0.5">
                Ko'rishlar soni: {movie?.views_count.toLocaleString()} marta
              </p>
            </div>
          </div>
        </div>

        {/* Asosiy ma'lumotlar formasi */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
              <Film className="w-5 h-5 text-indigo-500" /> Asosiy ma'lumotlar
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Turi (Kino yoki Serial) *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, content_type: 'movie' })}
                    className={`py-2.5 px-4 rounded-lg font-medium text-sm flex items-center justify-center gap-2 border transition-all ${
                      form.content_type === 'movie'
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    🎬 Kino
                  </button>
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, content_type: 'serial' })}
                    className={`py-2.5 px-4 rounded-lg font-medium text-sm flex items-center justify-center gap-2 border transition-all ${
                      form.content_type === 'serial'
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    📺 Serial
                  </button>
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {form.content_type === 'serial' ? 'Serial nomi *' : 'Kino nomi *'}
                </label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Original nomi
                </label>
                <input
                  value={form.original_title}
                  onChange={(e) => setForm({ ...form, original_title: e.target.value })}
                  className="input"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {form.content_type === 'serial' ? 'Serial Posteri' : 'Kino Posteri'}{' '}
                  <span className="text-xs text-indigo-500 font-normal">(Ixtiyoriy — majburiy emas)</span>
                </label>
                <div className="flex flex-col sm:flex-row gap-4 items-start">
                  <div className="flex-1 w-full space-y-2">
                    <input
                      value={form.poster_file_id}
                      onChange={(e) => setForm({ ...form, poster_file_id: e.target.value })}
                      className="input font-mono text-xs"
                      placeholder="Telegram file_id (AgAC...) yoki rasm linki (https://...)"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/60 p-2.5 rounded-lg border border-gray-100 dark:border-gray-700/60">
                      💡 <b>Rasm majburiy emas:</b> Agar rasm kiritmasangiz, botda video fayl va tugmalar
                      bevosita tavsif bilan birga yagona xabarda chiqadi. Agar rasm qo'ymoqchi bo'lsangiz,
                      botingizga rasm yuborib <code>file_id</code> oling yoki to'g'ridan-to'g'ri rasm havolasini (URL) qo'ying.
                    </p>
                  </div>

                  {form.poster_file_id && form.poster_file_id.startsWith('http') && (
                    <div className="w-24 h-32 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 shrink-0 flex items-center justify-center shadow-sm">
                      <img
                        src={form.poster_file_id}
                        alt="Poster preview"
                        className="w-full h-full object-cover"
                        onError={(e) => ((e.target as HTMLElement).style.display = 'none')}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tavsif (Qisqacha mazmun va syujet)
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="input min-h-28 resize-y"
                  placeholder="Film yoki serialning qisqacha mazmuni, rejissyor va bosh rollar haqida..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Chiqarilgan yili
                </label>
                <input
                  type="number"
                  value={form.year}
                  onChange={(e) => setForm({ ...form, year: e.target.value })}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Davlat / Mamlakat
                </label>
                <input
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  className="input"
                />
              </div>

              {form.content_type === 'serial' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Mavsumlar soni (Seasons)
                    </label>
                    <input
                      type="number"
                      value={form.total_seasons}
                      onChange={(e) => setForm({ ...form, total_seasons: e.target.value })}
                      className="input"
                      placeholder="Masalan: 3"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Qismlar soni (Episodes)
                    </label>
                    <input
                      type="number"
                      value={form.total_episodes}
                      onChange={(e) => setForm({ ...form, total_episodes: e.target.value })}
                      className="input"
                      placeholder="Masalan: 24"
                    />
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Davomiyligi (daqiqa)
                  </label>
                  <input
                    type="number"
                    value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
                    className="input"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  IMDb reytingi
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  value={form.imdb_rating}
                  onChange={(e) => setForm({ ...form, imdb_rating: e.target.value })}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Janrlar (vergul bilan ajrating)
                </label>
                <input
                  value={form.genres}
                  onChange={(e) => setForm({ ...form, genres: e.target.value })}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="input font-semibold"
                >
                  <option value="published">Nashr qilingan (Botda ko'rinadi)</option>
                  <option value="draft">Qoralama (Yashirin)</option>
                  <option value="hidden">Yashirilgan</option>
                </select>
              </div>
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}
            {savedSuccess && <p className="text-green-500 text-sm font-semibold">✓ Muvaffaqiyatli saqlandi!</p>}

            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" /> {updateMutation.isPending ? 'Saqlanmoqda...' : "O'zgarishlarni saqlash"}
            </button>
          </div>
        </form>

        {/* ------------------------------------------------------------------ */}
        {/* SERIAL QISMLARI BOSHQARUVI (EPISODES MANAGEMENT)                   */}
        {/* ------------------------------------------------------------------ */}
        {isSerial ? (
          <div className="card space-y-6 border-purple-200 dark:border-purple-900/40 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 rounded-xl">
                  <Tv className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    Serial Qismlari Boshqaruvi
                  </h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Jami qismlar: <span className="font-semibold text-purple-600 dark:text-purple-400">{movie?.episodes?.length || 0} ta</span>
                    {distinctSeasons.length > 0 && ` • Mavsumlar: ${distinctSeasons.join(', ')}-mavsum`}
                  </p>
                </div>
              </div>

              {/* Mode switchers */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-800 p-1 rounded-xl text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setEpisodeMode('list')}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    episodeMode === 'list'
                      ? 'bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-300 shadow-sm font-semibold'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <List className="w-3.5 h-3.5" /> Ro'yxat ({movie?.episodes?.length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setEpisodeMode('single')}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    episodeMode === 'single'
                      ? 'bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-300 shadow-sm font-semibold'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Plus className="w-3.5 h-3.5" /> Bitta qism
                </button>
                <button
                  type="button"
                  onClick={() => setEpisodeMode('batch')}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    episodeMode === 'batch'
                      ? 'bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-300 shadow-sm font-semibold'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" /> Tezkor yuklash
                </button>
              </div>
            </div>

            {batchSuccessMsg && (
              <div className="p-3 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm rounded-lg font-medium border border-green-200 dark:border-green-800">
                {batchSuccessMsg}
              </div>
            )}

            {/* TAB 1: BITTA QISM QO'SHISH (SINGLE EPISODE FORM) */}
            {episodeMode === 'single' && (
              <form onSubmit={handleSingleEpisodeSubmit} className="space-y-4 p-4 rounded-xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900/40">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Plus className="w-4 h-4 text-purple-600" /> Yangi qism qo'shish yoki yangilash
                  </h3>
                  <span className="text-xs text-gray-500">Auto-increment navbatdagi qism raqami tanlangan</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Mavsum (Season)
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={singleSeason}
                      onChange={(e) => setSingleSeason(Math.max(1, parseInt(e.target.value) || 1))}
                      className="input text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Qism raqami (Episode #)
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={singleEpNum}
                      onChange={(e) => {
                        const val = Math.max(1, parseInt(e.target.value) || 1);
                        setSingleEpNum(val);
                        if (!singleTitle || singleTitle.includes('-qism')) {
                          setSingleTitle(`${val}-qism`);
                        }
                      }}
                      className="input text-sm font-semibold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Sifat (Quality)
                    </label>
                    <select
                      value={singleQuality}
                      onChange={(e) => setSingleQuality(e.target.value)}
                      className="input text-sm font-semibold"
                    >
                      {QUALITIES.map((q) => (
                        <option key={q} value={q}>
                          🎥 {q}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Davomiyligi (daqiqa)
                    </label>
                    <input
                      type="number"
                      value={singleDuration}
                      onChange={(e) => setSingleDuration(e.target.value)}
                      className="input text-sm"
                      placeholder="45"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Qism nomi / Sarlavhasi (Ixtiyoriy)
                    </label>
                    <input
                      value={singleTitle}
                      onChange={(e) => setSingleTitle(e.target.value)}
                      className="input text-sm"
                      placeholder={`${singleEpNum}-qism`}
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Telegram video file_id *
                    </label>
                    <input
                      value={singleFileId}
                      onChange={(e) => setSingleFileId(e.target.value)}
                      className="input text-xs font-mono"
                      placeholder="BAACAgIAAxkBAAI..."
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={addEpisodeMut.isPending}
                    className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" /> {addEpisodeMut.isPending ? 'Qo\'shilmoqda...' : 'Qismni saqlash'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEpisodeMode('list')}
                    className="btn-secondary text-xs py-2 px-3"
                  >
                    Bekor qilish
                  </button>
                </div>
              </form>
            )}

            {/* TAB 2: TEZKOR / OMMAVIY QISMLAR QO'SHISH (BATCH UPLOAD) */}
            {episodeMode === 'batch' && (
              <form onSubmit={handleBatchEpisodeSubmit} className="space-y-4 p-4 rounded-xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900/40">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-600" /> Ommaviy qismlarni bir zumda yuklash (Batch)
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Telegram kanal yoki botdan olingan file_id larni har bir qatorda bittadan joylashtiring. Ular avtomatik tartib bilan 1-qism, 2-qism... qilib saqlanadi.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Mavsum raqami
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={batchSeason}
                      onChange={(e) => setBatchSeason(Math.max(1, parseInt(e.target.value) || 1))}
                      className="input text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Boshlang'ich qism raqami
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={batchStartEp}
                      onChange={(e) => setBatchStartEp(Math.max(1, parseInt(e.target.value) || 1))}
                      className="input text-sm font-semibold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Sifat (Barcha qismlar uchun)
                    </label>
                    <select
                      value={batchQuality}
                      onChange={(e) => setBatchQuality(e.target.value)}
                      className="input text-sm font-semibold"
                    >
                      {QUALITIES.map((q) => (
                        <option key={q} value={q}>
                          🎥 {q}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                      Telegram file_id lar (Har bir qatorda bitta video file_id):
                    </label>
                    {batchCount > 0 && (
                      <span className="text-xs bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 font-semibold px-2 py-0.5 rounded">
                        Aniqlangan qismlar: {batchCount} ta ({batchStartEp}-qismdan {batchStartEp + batchCount - 1}-qismgacha)
                      </span>
                    )}
                  </div>
                  <textarea
                    rows={6}
                    value={batchFileIds}
                    onChange={(e) => setBatchFileIds(e.target.value)}
                    className="input font-mono text-xs leading-relaxed"
                    placeholder={`BAACAgIAAxkBAAI...1\nBAACAgIAAxkBAAI...2\nBAACAgIAAxkBAAI...3`}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Masalan, agar 10 ta qator file_id tashlasangiz va boshlang'ich qism 1 bo'lsa, tizim 1-qismdan 10-qismgacha avtomatik yaratadi.
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={addBatchEpisodeMut.isPending || batchCount === 0}
                    className="btn-primary text-xs py-2 px-5 flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    {addBatchEpisodeMut.isPending
                      ? 'Yuklanmoqda...'
                      : `${batchCount > 0 ? `${batchCount} ta` : ''} Qismlarni yuklash`}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEpisodeMode('list')}
                    className="btn-secondary text-xs py-2 px-3"
                  >
                    Bekor qilish
                  </button>
                </div>
              </form>
            )}

            {/* TAB 3: MAVJUD QISMLAR RO'YXATI */}
            <div className="space-y-3">
              {/* Season filters */}
              {distinctSeasons.length > 1 && (
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  <button
                    type="button"
                    onClick={() => setSeasonFilter('all')}
                    className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                      seasonFilter === 'all'
                        ? 'bg-purple-600 text-white shadow-sm'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200'
                    }`}
                  >
                    Barcha mavsumlar ({movie?.episodes?.length || 0})
                  </button>
                  {distinctSeasons.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSeasonFilter(s)}
                      className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                        seasonFilter === s
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200'
                      }`}
                    >
                      {s}-mavsum ({movie?.episodes?.filter((e: Episode) => e.season_number === s).length})
                    </button>
                  ))}
                </div>
              )}

              {filteredEpisodes.length === 0 ? (
                <div className="text-center py-10 border border-dashed border-gray-200 dark:border-gray-800 rounded-xl space-y-3">
                  <Tv className="w-10 h-10 text-gray-400 mx-auto" />
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Hozircha qismlar yuklanmagan
                    </h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Serial uchun 1-qism, 2-qism... kabi qismlarni bittalab yoki ommaviy yuklashingiz mumkin
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <button
                      type="button"
                      onClick={() => setEpisodeMode('single')}
                      className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" /> Bitta qism qo'shish
                    </button>
                    <button
                      type="button"
                      onClick={() => setEpisodeMode('batch')}
                      className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
                    >
                      <Sparkles className="w-3.5 h-3.5" /> Tezkor ommaviy yuklash
                    </button>
                  </div>
                </div>
              ) : (
                <div className="overflow-x-auto border border-gray-100 dark:border-gray-800 rounded-xl">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-gray-500 bg-gray-50/70 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                        <th className="py-2.5 px-3 font-semibold">Qism</th>
                        <th className="py-2.5 px-3 font-semibold">Mavsum</th>
                        <th className="py-2.5 px-3 font-semibold">Nomi</th>
                        <th className="py-2.5 px-3 font-semibold">Sifati</th>
                        <th className="py-2.5 px-3 font-semibold">Telegram file_id</th>
                        <th className="py-2.5 px-3 font-semibold">Ko'rishlar</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Amallar</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                      {filteredEpisodes.map((ep: Episode) => (
                        <tr
                          key={ep.id}
                          className="hover:bg-gray-50/50 dark:hover:bg-gray-800/40 transition-colors"
                        >
                          <td className="py-2.5 px-3 font-bold text-gray-900 dark:text-white">
                            <span className="bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded font-mono">
                              #{ep.episode_number}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 dark:text-gray-400 font-medium">
                            {ep.season_number}-mavsum
                          </td>
                          <td className="py-2.5 px-3 text-gray-800 dark:text-gray-200 font-medium">
                            {ep.title || `${ep.episode_number}-qism`}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded font-semibold text-[11px]">
                              {ep.quality}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 font-mono text-gray-400">
                            <div className="flex items-center gap-1.5 max-w-[200px] sm:max-w-xs">
                              <span className="truncate">{ep.telegram_file_id}</span>
                              <button
                                type="button"
                                onClick={() => copyToClipboard(ep.telegram_file_id, ep.id)}
                                className="p-1 hover:text-white text-gray-400 hover:bg-gray-700 rounded transition-colors shrink-0"
                                title="Nusxa olish"
                              >
                                {copiedId === ep.id ? (
                                  <Check className="w-3.5 h-3.5 text-green-500" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </td>
                          <td className="py-2.5 px-3 text-gray-500 font-mono">
                            {ep.views_count.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <button
                              type="button"
                              onClick={() => {
                                if (
                                  confirm(
                                    `${ep.season_number}-mavsum, ${ep.episode_number}-qismni o'chirmoqchimisiz?`
                                  )
                                ) {
                                  deleteEpisodeMut.mutate(ep.id);
                                }
                              }}
                              className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                              title="O'chirish"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ------------------------------------------------------------------ */
          /* KINO VIDEO SIFATLARI BOSHQARUVI (MOVIE QUALITY VARIANTS)           */
          /* ------------------------------------------------------------------ */
          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
              <Video className="w-5 h-5 text-indigo-500" /> Mavjud video sifatlar
            </h2>

            <div className="space-y-2">
              {movie?.videos && movie.videos.length > 0 ? (
                movie.videos.map((vid: any) => (
                  <div
                    key={vid.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-sm bg-indigo-500 text-white px-2 py-0.5 rounded">
                        {vid.quality}
                      </span>
                      <code className="text-xs font-mono text-gray-400 truncate max-w-xs sm:max-w-md">
                        {vid.telegram_file_id}
                      </code>
                    </div>
                    <button
                      onClick={() => {
                        if (confirm(`"${vid.quality}" sifatdagi videoni o'chirilsinmi?`)) {
                          deleteVideoMut.mutate(vid.id);
                        }
                      }}
                      className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-400">Videolar yo'q</p>
              )}
            </div>

            <form
              onSubmit={handleAddVideo}
              className="pt-3 border-t border-gray-100 dark:border-gray-800 flex flex-col sm:flex-row gap-3 items-end"
            >
              <div className="w-full sm:w-36">
                <label className="block text-xs font-semibold text-gray-500 mb-1">Yangi sifat</label>
                <select
                  value={newQuality}
                  onChange={(e) => setNewQuality(e.target.value)}
                  className="input text-sm font-semibold"
                >
                  {QUALITIES.map((q) => (
                    <option key={q} value={q}>
                      🎥 {q}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1 w-full">
                <label className="block text-xs font-semibold text-gray-500 mb-1">Telegram file_id</label>
                <input
                  value={newFileId}
                  onChange={(e) => setNewFileId(e.target.value)}
                  className="input text-xs font-mono"
                  placeholder="Telegram video file_id..."
                  required
                />
              </div>
              <button
                type="submit"
                disabled={addVideoMut.isPending}
                className="btn-secondary flex items-center gap-1.5 text-xs py-2 px-3 whitespace-nowrap"
              >
                <Plus className="w-4 h-4" /> Sifat qo'shish
              </button>
            </form>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
