'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createMovie } from '@/services/api';
import { useRouter } from 'next/navigation';
import { Plus, Trash2, Film, ArrowLeft, Image as ImageIcon, Tv, Sparkles } from 'lucide-react';
import Link from 'next/link';

const QUALITIES = ['360p', '480p', '720p', '1080p', '4K'];

export default function NewMoviePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
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
  const [videos, setVideos] = useState<{ quality: string; telegram_file_id: string }[]>([
    { quality: '720p', telegram_file_id: '' },
  ]);
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: createMovie,
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['movies'] });
      if (data?.content_type === 'serial') {
        router.push(`/movies/${data.id}`);
      } else {
        router.push('/movies');
      }
    },
    onError: (e: any) => setError(e.response?.data?.detail || "Kino/serial qo'shishda xatolik yuz berdi"),
  });

  const addVideo = () => setVideos([...videos, { quality: '1080p', telegram_file_id: '' }]);
  const removeVideo = (i: number) => setVideos(videos.filter((_, idx) => idx !== i));
  const updateVideo = (i: number, k: string, v: string) =>
    setVideos(videos.map((vid, idx) => (idx === i ? { ...vid, [k]: v } : vid)));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const validVideos = videos.filter((v) => v.telegram_file_id.trim());
    if (form.content_type === 'movie' && validVideos.length === 0) {
      setError("Kamida bitta video telegram_file_id si kiritilishi shart!");
      return;
    }

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
      videos: validVideos,
    };
    mutation.mutate(data);
  };

  return (
    <AdminLayout>
      <div className="max-w-3xl space-y-6 pb-12">
        <div className="flex items-center gap-3">
          <Link href="/movies" className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Yangi kino qo'shish</h1>
            <p className="text-gray-500 text-sm">Film ma'lumotlari va sifat bo'yicha video fayllarni kiriting</p>
          </div>
        </div>

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
                  placeholder={form.content_type === 'serial' ? "Masalan: Qashqirlar makoni" : "Masalan: Interstellar"}
                  required
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Original nomi (inglizcha yoki boshqa)
                </label>
                <input
                  value={form.original_title}
                  onChange={(e) => setForm({ ...form, original_title: e.target.value })}
                  className="input"
                  placeholder="Masalan: Interstellar"
                />
              </div>


              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Chiqarilgan yili</label>
                <input
                  type="number"
                  value={form.year}
                  onChange={(e) => setForm({ ...form, year: e.target.value })}
                  className="input"
                  placeholder="2024"
                  min="1900"
                  max="2035"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Davlat / Mamlakat</label>
                <input
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  className="input"
                  placeholder="AQSH, Buyuk Britaniya"
                />
              </div>

              {form.content_type === 'serial' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mavsumlar soni (Seasons)</label>
                    <input
                      type="number"
                      value={form.total_seasons}
                      onChange={(e) => setForm({ ...form, total_seasons: e.target.value })}
                      className="input"
                      placeholder="Masalan: 3"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Qismlar soni (Episodes)</label>
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Davomiyligi (daqiqa)</label>
                  <input
                    type="number"
                    value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
                    className="input"
                    placeholder="169"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">IMDb reytingi</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  value={form.imdb_rating}
                  onChange={(e) => setForm({ ...form, imdb_rating: e.target.value })}
                  className="input"
                  placeholder="8.7"
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
                  placeholder="Fantastika, Drama, Sarguzasht"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="input font-medium"
                >
                  <option value="published">Nashr qilingan (Botda ko'rinadi)</option>
                  <option value="draft">Qoralama (Yashirin)</option>
                  <option value="hidden">Yashirilgan</option>
                </select>
              </div>
            </div>
          </div>

          {/* Rasm (Poster) va Tavsif bo'limi */}
          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
              <ImageIcon className="w-5 h-5 text-indigo-500" /> Rasm (Poster) va Tavsif
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Kino / Serial Posteri <span className="text-xs text-indigo-500 font-normal">(Ixtiyoriy — majburiy emas)</span>
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
                      💡 <b>Rasm majburiy emas:</b> Agar rasm kiritmasangiz, botda video fayl va tugmalar bevosita kino tavsifi bilan birga yagona xabarda chiqadi. Agar rasm qo'ymoqchi bo'lsangiz, botingizga (@KINOMEDIA_RASMIY_bot) rasm yuborib <code>file_id</code> oling yoki to'g'ridan-to'g'ri rasm havolasini (URL) qo'ying.
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

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tavsif (Qisqacha syujet va film haqida)
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="input min-h-28 resize-y"
                  placeholder="Film yoki serialning qisqacha mazmuni, rejissyor va bosh rollar haqida..."
                />
              </div>
            </div>
          </div>

          {form.content_type === 'movie' ? (
            <div className="card space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
                <div>
                  <h2 className="font-semibold text-gray-900 dark:text-white">🎥 Video fayllar va sifatlar</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Admin bitta kino uchun bir nechta sifat qo'shishi mumkin</p>
                </div>
                <button
                  type="button"
                  onClick={addVideo}
                  className="btn-secondary flex items-center gap-1.5 text-xs py-1.5"
                >
                  <Plus className="w-3.5 h-3.5" /> Sifat qo'shish
                </button>
              </div>

              <div className="space-y-3">
                {videos.map((v, i) => (
                  <div key={i} className="flex flex-col sm:flex-row gap-3 items-start sm:items-end p-3 rounded-lg bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800">
                    <div className="w-full sm:w-36">
                      <label className="block text-xs font-semibold text-gray-500 mb-1">Video Sifati</label>
                      <select
                        value={v.quality}
                        onChange={(e) => updateVideo(i, 'quality', e.target.value)}
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
                      <label className="block text-xs font-semibold text-gray-500 mb-1">
                        Telegram video file_id *
                      </label>
                      <input
                        value={v.telegram_file_id}
                        onChange={(e) => updateVideo(i, 'telegram_file_id', e.target.value)}
                        className="input text-xs font-mono"
                        placeholder="BAACAgIAAxkBAAI..."
                        required
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeVideo(i)}
                      className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      title="O'chirish"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card space-y-3 bg-purple-50/50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-900/40">
              <div className="flex items-start gap-3">
                <div className="p-2.5 bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400 rounded-xl shrink-0 mt-0.5">
                  <Tv className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    📺 Serial Qismlari Boshqaruvi
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">
                    Serial saqlangach, darhol ochiladigan maxsus qismlar boshqaruv panelida (1-mavsum, 2-mavsum...) qismlarni <b>bittalab</b> yoki <b>ommaviy (bir zumda 10-20 ta qismni)</b> yuklashingiz mumkin.
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm font-medium">
              {error}
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn-primary flex items-center gap-2 px-6"
            >
              {mutation.isPending
                ? 'Saqlanmoqda...'
                : form.content_type === 'serial'
                ? "Serialni saqlash va qismlariga o'tish →"
                : "Kinoni saqlash va kod yaratish"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="btn-secondary"
            >
              Bekor qilish
            </button>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}
