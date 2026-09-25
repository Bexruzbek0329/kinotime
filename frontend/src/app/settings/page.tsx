'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, syncTelegramSettings } from '@/services/api';
import { useState, useEffect } from 'react';
import {
  Settings,
  Save,
  Sparkles,
  MessageSquare,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Bot,
  Info,
} from 'lucide-react';

const TEXT_KEYS = [
  { key: 'welcome_message', label: '/start xush kelibsiz matni', desc: 'Foydalanuvchi START bosgandan so\'ng yuboriladi' },
  { key: 'not_found_message', label: 'Kino topilmaganda matn', desc: 'Qidiruv natijasiz tugaganda' },
  { key: 'error_message', label: 'Xatolik yuz bergandagi matn', desc: 'Texnik xatolik paytida' },
  { key: 'help_message', label: 'Yordam bo\'limi matni', desc: 'ℹ️ Yordam bosilganda chiqadigan matn' },
  { key: 'subscription_message', label: 'Majburiy obuna matni', desc: 'Kanalga obuna bo\'lmagan foydalanuvchiga' },
  { key: 'admin_contact', label: 'Admin bog\'lanish havolasi (URL)', desc: 'Masalan: https://t.me/admin_username' },
];

const STICKER_KEYS = [
  { key: 'start_sticker_file_id', label: 'Start / Welcome Sticker', desc: '/start buyrug\'ida yuboriladi' },
  { key: 'not_found_sticker_file_id', label: 'Topilmadi Sticker', desc: 'Kino qidiruvda topilmaganda yuboriladi' },
  { key: 'error_sticker_file_id', label: 'Xato Sticker', desc: 'Kutilmagan xatolikda' },
  { key: 'movie_sticker_file_id', label: 'Kino ochilganda Sticker', desc: 'Film kartasi ochilishidan oldin' },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: rawSettings } = useQuery({ queryKey: ['settings'], queryFn: getSettings });
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    if (rawSettings) setSettings(rawSettings);
  }, [rawSettings]);

  const saveMut = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
  });

  const handleSyncTelegram = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      // First save current form settings
      await updateSettings(settings);
      const res = await syncTelegramSettings();
      if (res.ok) {
        setSyncStatus({ ok: true, message: 'Telegram bilan muvaffaqiyatli sinxronlandi!' });
      } else {
        setSyncStatus({ ok: false, message: res.error || 'Telegramga sinxronlashda xatolik yuz berdi' });
      }
    } catch (err: unknown) {
      const errorMsg =
        (err && typeof err === 'object' && 'response' in err && (err as { response?: { data?: { detail?: string } } }).response?.data?.detail) ||
        (err instanceof Error ? err.message : 'Xatolik yuz berdi');
      setSyncStatus({ ok: false, message: String(errorMsg) });
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncStatus(null), 4000);
    }
  };

  const setVal = (k: string, v: string) => setSettings((p) => ({ ...p, [k]: v }));

  const botDescValue = settings['bot_description'] ?? '';
  const botShortDescValue = settings['bot_short_description'] ?? '';

  return (
    <AdminLayout>
      <div className="max-w-4xl space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Settings className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Bot Sozlamalari</h1>
              <p className="text-gray-500 text-sm">Bot tavsifi, matnlari va stikerlarini boshqarish</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSyncTelegram}
              disabled={syncing || saveMut.isPending}
              className="btn-secondary flex items-center gap-2 text-xs py-2 px-3 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400"
              title="Telegram Bot API (setMyDescription) ga yuborish"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Sinxronlanmoqda...' : 'Telegramga sinxronlash'}
            </button>

            <button
              onClick={() => saveMut.mutate(settings)}
              disabled={saveMut.isPending}
              className="btn-primary flex items-center justify-center gap-2 text-xs py-2 px-4"
            >
              <Save className="w-4 h-4" />
              {saved ? '✓ Saqlandi!' : saveMut.isPending ? 'Saqlanmoqda...' : 'Barchasini saqlash'}
            </button>
          </div>
        </div>

        {/* Sync Toast / Notification */}
        {syncStatus && (
          <div
            className={`p-3.5 rounded-xl border flex items-center gap-3 text-xs transition-all ${
              syncStatus.ok
                ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                : 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300'
            }`}
          >
            {syncStatus.ok ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            )}
            <span className="font-medium">{syncStatus.message}</span>
          </div>
        )}

        {/* 1. STARTDAN OLDINGI OYNA ("What can this bot do?") */}
        <div className="card space-y-5 border-2 border-indigo-500/20 bg-gradient-to-br from-indigo-500/[0.03] via-transparent to-purple-500/[0.03]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800 gap-2">
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 text-base">
                <Sparkles className="w-5 h-5 text-indigo-500" />
                Startdan oldingi oyna — &quot;What can this bot do?&quot;
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Foydalanuvchi botga kirganda START tugmasini bosishidan oldin ko&apos;rinadigan oyna matni va stikeri
              </p>
            </div>
            <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 self-start sm:self-auto">
              Telegram Bot API (setMyDescription)
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Form Fields */}
            <div className="lg:col-span-7 space-y-4">
              {/* Bot Description */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                    Oyna tavsifi (&quot;What can this bot do?&quot; matni)
                  </label>
                  <span
                    className={`text-[11px] font-mono ${
                      botDescValue.length > 480
                        ? 'text-amber-500 font-bold'
                        : 'text-gray-400'
                    }`}
                  >
                    {botDescValue.length} / 512 belgi
                  </span>
                </div>
                <textarea
                  value={botDescValue}
                  onChange={(e) => setVal('bot_description', e.target.value)}
                  maxLength={512}
                  rows={6}
                  className="input resize-y font-mono text-xs leading-relaxed"
                  placeholder={'🎬 Kinolar Olami Botiga xush kelibsiz!\n\nBu yerda eng so\'nggi premyeralar va filmlarni topishingiz mumkin.\n\nBoshlash uchun START tugmasini bosing! 👇'}
                />
                <p className="text-[11px] text-gray-400">
                  Ushbu matn Telegramda chat bo&apos;sh bo&apos;lganda ko&apos;rinadi. Emoji va yangi qatorlar qo&apos;llab-quvvatlanadi.
                </p>
              </div>

              {/* Bot Short Description */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                    Bot qisqa tavsifi (Short description)
                  </label>
                  <span className="text-[11px] font-mono text-gray-400">
                    {botShortDescValue.length} / 120 belgi
                  </span>
                </div>
                <input
                  value={botShortDescValue}
                  onChange={(e) => setVal('bot_short_description', e.target.value)}
                  maxLength={120}
                  className="input text-xs"
                  placeholder="Eng sara kino va seriallar olami 🎬"
                />
                <p className="text-[11px] text-gray-400">
                  Bot profili ochilganda va bot havolasi do&apos;stlarga yuborilganda ko&apos;rinadigan qisqa tavsif.
                </p>
              </div>

              {/* BotFather Instructions for Sticker / Picture */}
              <div className="rounded-xl border border-indigo-200/80 dark:border-indigo-900/60 bg-indigo-50/60 dark:bg-indigo-950/30 p-3.5 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-950 dark:text-indigo-200 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-indigo-500" />
                    Stiker yoki Rasm qo&apos;yish (Telegram talabi)
                  </span>
                  <a
                    href="https://t.me/BotFather"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    @BotFather ga o&apos;tish <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <p className="text-[11px] text-gray-600 dark:text-gray-300 leading-relaxed">
                  Telegram xavfsizlik qoidalariga binoan, <b>&quot;What can this bot do?&quot;</b> oynasi tepasiga <b>animatsiyali stiker, GIF yoki rasm</b> joylash faqat rasmiy <b>@BotFather</b> orqali amalga oshiriladi:
                </p>
                <ol className="text-[11px] text-gray-700 dark:text-gray-300 space-y-1 list-decimal list-inside bg-white/80 dark:bg-gray-900/60 p-2.5 rounded-lg border border-indigo-100 dark:border-indigo-900/50">
                  <li><b>@BotFather</b> ga kiring va <code>/mybots</code> buyrug&apos;ini yuboring</li>
                  <li>Botingizni tanlang: <b>KINOMEDIA_RASMIY_bot</b></li>
                  <li><b>Edit Bot</b> ➡️ <b>Edit Description Picture</b> bo&apos;limini bosing</li>
                  <li>Stiker (TGS), animatsiyali GIF yoki rasm (640x360 px) yuboring</li>
                </ol>
                <p className="text-[10px] text-indigo-600 dark:text-indigo-400 italic">
                  💡 Shunda Telegram ushbu matn tepasida siz yuklagan stikerni chiroyli qilib namoyish etadi.
                </p>
              </div>
            </div>

            {/* Right Column: Live Telegram Mockup */}
            <div className="lg:col-span-5 space-y-2">
              <label className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                <Bot className="w-4 h-4 text-indigo-500" />
                Telegramda ko&apos;rinish namunasi (Jonli prevyu)
              </label>

              {/* Mockup Frame */}
              <div className="rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-800 shadow-md bg-[#0e1621] text-white select-none">
                {/* Telegram Chat Header */}
                <div className="bg-[#17212b] px-3.5 py-2.5 border-b border-[#232e3c] flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xs text-white shadow-inner">
                    🎬
                  </div>
                  <div>
                    <div className="font-semibold text-xs leading-tight text-white">Kinolar Olami Bot</div>
                    <div className="text-[10px] text-gray-400">bot</div>
                  </div>
                </div>

                {/* Telegram Chat Area */}
                <div className="p-4 min-h-[220px] flex flex-col justify-end relative bg-[radial-gradient(#1e2c3a_1px,transparent_1px)] [background-size:16px_16px]">
                  {/* Chat Bubble */}
                  <div className="bg-[#182533] border border-[#2b394a] rounded-2xl p-3.5 max-w-[95%] shadow-lg space-y-2">
                    <div className="text-xs font-bold text-white flex items-center gap-1.5">
                      <span>What can this bot do?</span>
                    </div>

                    <div className="text-xs text-gray-200 whitespace-pre-wrap leading-relaxed font-sans">
                      {botDescValue.trim() ? (
                        botDescValue
                      ) : (
                        <span className="text-gray-500 italic">
                          Tavsif matni kiritilmagan. Chap tarafdagi maydonga matn kiriting...
                        </span>
                      )}
                    </div>
                  </div>

                  {/* START Button */}
                  <div className="mt-4 pt-2">
                    <div className="w-full bg-[#2b5278] hover:bg-[#32608c] text-white text-xs font-semibold py-2.5 rounded-xl text-center uppercase tracking-wider transition-colors shadow">
                      START
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-[11px] text-gray-400 text-center">
                Telegram ilovasida foydalanuvchiga xuddi shu ko&apos;rinishda aks etadi.
              </p>
            </div>
          </div>
        </div>

        {/* 2. STICKERLAR BOSHQARUVI */}
        <div className="card space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-500" /> 🎨 Bot ichidagi stikerlar boshqaruvi
            </h2>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold">
              <span>Stikerlarni yoqish:</span>
              <input
                type="checkbox"
                checked={settings['stickers_enabled'] === 'true'}
                onChange={(e) => setVal('stickers_enabled', e.target.checked ? 'true' : 'false')}
                className="w-4 h-4 accent-indigo-600 rounded"
              />
            </label>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {STICKER_KEYS.map(({ key, label, desc }) => (
              <div key={key} className="space-y-1">
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                  {label}
                </label>
                <input
                  value={settings[key] ?? ''}
                  onChange={(e) => setVal(key, e.target.value)}
                  className="input font-mono text-xs"
                  placeholder="Telegram sticker file_id..."
                />
                <p className="text-[11px] text-gray-400">{desc}</p>
              </div>
            ))}
          </div>

          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-2.5 text-[11px] text-gray-500 flex items-start gap-2">
            <Info className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
            <span>
              <b>Stiker file_id olish usuli:</b> Telegramda o&apos;zingizning admin hisobingizdan botga istalgan stikerni yuborsangiz, bot sizga uning <code>file_id</code> sini darhol yuboradi. O&apos;sha kodni nusxalab bu yerga joylaysiz.
            </span>
          </div>
        </div>

        {/* 3. BOT MATNLARI (Markdown) */}
        <div className="card space-y-5">
          <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
            <MessageSquare className="w-5 h-5 text-indigo-500" /> 📝 Bot xabar matnlari (Markdown)
          </h2>

          {TEXT_KEYS.map(({ key, label, desc }) => (
            <div key={key} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                  {label}
                </label>
                <span className="text-[11px] text-gray-400">{desc}</span>
              </div>
              {key === 'admin_contact' ? (
                <input
                  value={settings[key] ?? ''}
                  onChange={(e) => setVal(key, e.target.value)}
                  className="input text-xs"
                  placeholder="https://t.me/admin"
                />
              ) : (
                <textarea
                  value={settings[key] ?? ''}
                  onChange={(e) => setVal(key, e.target.value)}
                  className="input min-h-24 resize-y font-mono text-xs leading-relaxed"
                />
              )}
            </div>
          ))}
        </div>

        {/* Bottom Save Button */}
        <div className="flex justify-end gap-3">
          <button
            onClick={handleSyncTelegram}
            disabled={syncing || saveMut.isPending}
            className="btn-secondary flex items-center gap-2 px-4"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            Telegramga sinxronlash
          </button>

          <button
            onClick={() => saveMut.mutate(settings)}
            disabled={saveMut.isPending}
            className="btn-primary flex items-center gap-2 px-6"
          >
            <Save className="w-4 h-4" />
            {saved ? '✓ Saqlandi!' : saveMut.isPending ? 'Saqlanmoqda...' : 'Barchasini saqlash'}
          </button>
        </div>
      </div>
    </AdminLayout>
  );
}
