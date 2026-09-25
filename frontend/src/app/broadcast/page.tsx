'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { sendBroadcast, getBroadcastStatus, getSettings, updateSettings } from '@/services/api';
import {
  Megaphone,
  Send,
  CheckCircle,
  Info,
  Plus,
  Trash2,
  ExternalLink,
  Users,
  Zap,
  UserCheck,
  Pin,
  BellOff,
  Eye,
  Tv,
  Sparkles,
  Save,
  HelpCircle,
} from 'lucide-react';
import Link from 'next/link';

interface InlineButton {
  text: string;
  url: string;
}

export default function BroadcastPage() {
  const [activeTab, setActiveTab] = useState<'broadcast' | 'sponsor'>('broadcast');

  // Broadcast state
  const [text, setText] = useState('');
  const [parseMode, setParseMode] = useState<'Markdown' | 'HTML'>('Markdown');
  const [photoFileId, setPhotoFileId] = useState('');
  const [videoFileId, setVideoFileId] = useState('');
  const [targetAudience, setTargetAudience] = useState<'all' | 'active' | 'test_admin'>('all');
  const [pinMessage, setPinMessage] = useState(false);
  const [disableNotification, setDisableNotification] = useState(false);
  const [buttons, setButtons] = useState<InlineButton[]>([]);
  const [broadcastId, setBroadcastId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Sponsor ad state
  const { data: rawSettings, refetch: refetchSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });
  const [sponsorSettings, setSponsorSettings] = useState({
    sponsor_ad_enabled: 'false',
    sponsor_ad_text: '',
    sponsor_ad_button_text: '',
    sponsor_ad_button_url: '',
  });
  const [sponsorSaved, setSponsorSaved] = useState(false);

  // Sync sponsor settings from query
  useState(() => {
    if (rawSettings) {
      setSponsorSettings({
        sponsor_ad_enabled: rawSettings['sponsor_ad_enabled'] || 'false',
        sponsor_ad_text: rawSettings['sponsor_ad_text'] || '',
        sponsor_ad_button_text: rawSettings['sponsor_ad_button_text'] || '',
        sponsor_ad_button_url: rawSettings['sponsor_ad_button_url'] || '',
      });
    }
  });

  const saveSponsorMut = useMutation({
    mutationFn: (data: any) => updateSettings(data),
    onSuccess: () => {
      refetchSettings();
      setSponsorSaved(true);
      setTimeout(() => setSponsorSaved(false), 3000);
    },
  });

  const sendMut = useMutation({
    mutationFn: sendBroadcast,
    onSuccess: async (data) => {
      setBroadcastId(data.broadcast_id);
      setErrorMsg('');
      const poll = setInterval(async () => {
        try {
          const s = await getBroadcastStatus(data.broadcast_id);
          setStatus(s);
          if (s.done) clearInterval(poll);
        } catch {
          clearInterval(poll);
        }
      }, 1500);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Xatolik yuz berdi");
    },
  });

  const handleAddButton = () => {
    setButtons([...buttons, { text: '', url: '' }]);
  };

  const handleUpdateButton = (index: number, field: 'text' | 'url', value: string) => {
    const updated = [...buttons];
    updated[index][field] = value;
    setButtons(updated);
  };

  const handleRemoveButton = (index: number) => {
    setButtons(buttons.filter((_, i) => i !== index));
  };

  const handleInsertTag = (open: string, close: string) => {
    setText((prev) => prev + `${open}matn${close}`);
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setErrorMsg('');
    setBroadcastId(null);
    setStatus(null);

    const validButtons = buttons.filter((b) => b.text.trim() && b.url.trim());

    sendMut.mutate({
      text: text.trim(),
      parse_mode: parseMode,
      photo_file_id: photoFileId.trim() || undefined,
      video_file_id: videoFileId.trim() || undefined,
      buttons: validButtons.length > 0 ? validButtons : undefined,
      pin_message: pinMessage,
      disable_notification: disableNotification,
      target_audience: targetAudience,
    });
  };

  return (
    <AdminLayout>
      <div className="max-w-4xl space-y-6 pb-16">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Megaphone className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reklama Markazi</h1>
              <p className="text-gray-500 text-sm">Ommaviy xabarnomalar va doimiy homiylik reklamalarini boshqarish</p>
            </div>
          </div>

          {/* Section Switcher */}
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 p-1 rounded-xl text-xs font-semibold self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('broadcast')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                activeTab === 'broadcast'
                  ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Megaphone className="w-4 h-4" /> Ommaviy Xabarnoma
            </button>
            <button
              onClick={() => setActiveTab('sponsor')}
              className={`px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                activeTab === 'sponsor'
                  ? 'bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Tv className="w-4 h-4" /> Doimiy Homiy (Video ostida)
            </button>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* SECTION 1: OMMAVIY XABARNOMA (BROADCAST)                          */}
        {/* ---------------------------------------------------------------- */}
        {activeTab === 'broadcast' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Form Column */}
            <div className="lg:col-span-7 space-y-5">
              <form onSubmit={handleSend} className="card space-y-4">
                {/* Target Audience Tabs */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                    Kimlarga yuboriladi (Targeting):
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setTargetAudience('all')}
                      className={`p-2.5 rounded-xl border text-xs font-medium flex flex-col items-center gap-1 transition-all ${
                        targetAudience === 'all'
                          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      <Users className="w-4 h-4" />
                      <span>Barcha a'zolar</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setTargetAudience('active')}
                      className={`p-2.5 rounded-xl border text-xs font-medium flex flex-col items-center gap-1 transition-all ${
                        targetAudience === 'active'
                          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      <Zap className="w-4 h-4" />
                      <span>Faol (30 kun)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setTargetAudience('test_admin')}
                      className={`p-2.5 rounded-xl border text-xs font-medium flex flex-col items-center gap-1 transition-all ${
                        targetAudience === 'test_admin'
                          ? 'border-amber-600 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                      title="Xabarni avval o'z Telegram profilingizda sinov tariqasida ko'rish"
                    >
                      <UserCheck className="w-4 h-4" />
                      <span>Adminga sinov</span>
                    </button>
                  </div>
                  {targetAudience === 'test_admin' && (
                    <p className="text-[11px] text-amber-600 dark:text-amber-400 mt-1.5 flex items-center gap-1">
                      💡 <b>Sinov rejimi:</b> Xabar boshqalarga bormaydi, faqat profilingizga Telegram orqali yuboriladi.
                    </p>
                  )}
                </div>

                {/* Message Text with Toolbar */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                      Xabar matni * ({parseMode})
                    </label>
                    <div className="flex items-center gap-1 text-[11px]">
                      <button
                        type="button"
                        onClick={() => handleInsertTag('*', '*')}
                        className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 font-bold"
                      >
                        B
                      </button>
                      <button
                        type="button"
                        onClick={() => handleInsertTag('_', '_')}
                        className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 italic"
                      >
                        I
                      </button>
                      <button
                        type="button"
                        onClick={() => setText((p) => p + '[Tugma matni](https://t.me/...)')}
                        className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 text-indigo-500"
                      >
                        Link
                      </button>
                      <button
                        type="button"
                        onClick={() => setText((p) => p + '`kod`')}
                        className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 font-mono"
                      >
                        Code
                      </button>
                    </div>
                  </div>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={5}
                    className="input font-mono text-xs leading-relaxed"
                    placeholder="🔥 *Katta chegirma yoki Yangilik!*\n\nKanalimiz a'zolari uchun maxsus premyeralar taqdimoti boshlandi."
                    required
                  />
                </div>

                {/* Media IDs */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Rasm (photo file_id)
                    </label>
                    <input
                      value={photoFileId}
                      onChange={(e) => {
                        setPhotoFileId(e.target.value);
                        if (e.target.value) setVideoFileId('');
                      }}
                      className="input font-mono text-xs"
                      placeholder="AgACAgIAAxk..."
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Video (video file_id)
                    </label>
                    <input
                      value={videoFileId}
                      onChange={(e) => {
                        setVideoFileId(e.target.value);
                        if (e.target.value) setPhotoFileId('');
                      }}
                      className="input font-mono text-xs"
                      placeholder="BAACAgIAAxk..."
                    />
                  </div>
                </div>

                {/* Inline URL Buttons */}
                <div className="space-y-2 pt-2 border-t border-gray-100 dark:border-gray-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                        🔘 Inline Reklama Tugmalari (URL Buttons)
                      </label>
                      <p className="text-[11px] text-gray-400">Telegram xabari tagida bosiladigan havolalar</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddButton}
                      className="btn-secondary text-[11px] py-1 px-2.5 flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" /> Tugma qo'shish
                    </button>
                  </div>

                  {buttons.map((btn, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800"
                    >
                      <input
                        value={btn.text}
                        onChange={(e) => handleUpdateButton(idx, 'text', e.target.value)}
                        className="input text-xs flex-1"
                        placeholder="Tugma matni (masalan: Kanalga obuna bo'lish)"
                        required
                      />
                      <input
                        value={btn.url}
                        onChange={(e) => handleUpdateButton(idx, 'url', e.target.value)}
                        className="input text-xs flex-1 font-mono"
                        placeholder="https://t.me/kanal yoki https://sayt.uz"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveButton(idx)}
                        className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Options: Pin & Silent */}
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100 dark:border-gray-800">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={pinMessage}
                      onChange={(e) => setPinMessage(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600"
                    />
                    <Pin className="w-3.5 h-3.5 text-indigo-500" />
                    <span>Chatga qadash (Pin)</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={disableNotification}
                      onChange={(e) => setDisableNotification(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600"
                    />
                    <BellOff className="w-3.5 h-3.5 text-gray-400" />
                    <span>Ovozsiz (Silent)</span>
                  </label>
                </div>

                {errorMsg && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-xs rounded-lg font-medium border border-red-200 dark:border-red-900">
                    {errorMsg}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={sendMut.isPending}
                  className="btn-primary flex items-center justify-center gap-2 w-full py-2.5 font-semibold text-sm"
                >
                  <Send className="w-4 h-4" />
                  {sendMut.isPending
                    ? 'Yuborilmoqda...'
                    : targetAudience === 'test_admin'
                    ? 'Adminga sinov xabarini yuborish'
                    : "Xabarnomani barchaga jo'natish"}
                </button>
              </form>
            </div>

            {/* Preview & Stats Column */}
            <div className="lg:col-span-5 space-y-4">
              {/* Telegram Live Preview */}
              <div className="card space-y-3 bg-[#0e1621] text-white border-[#1e2c3a]">
                <div className="flex items-center justify-between border-b border-[#232e3c] pb-2">
                  <span className="text-xs font-semibold flex items-center gap-1.5 text-gray-300">
                    <Eye className="w-4 h-4 text-indigo-400" /> Jonli Telegram Ko'rinishi
                  </span>
                  <span className="text-[10px] text-gray-400">Prevyu</span>
                </div>

                {/* Chat Bubble */}
                <div className="bg-[#182533] border border-[#2b394a] rounded-2xl p-3.5 space-y-2 shadow-lg">
                  {photoFileId && (
                    <div className="h-32 bg-[#232e3c] rounded-lg flex items-center justify-center text-xs text-gray-400">
                      🖼️ Rasm ({photoFileId.slice(0, 12)}...)
                    </div>
                  )}
                  {videoFileId && (
                    <div className="h-32 bg-[#232e3c] rounded-lg flex items-center justify-center text-xs text-gray-400">
                      🎥 Video ({videoFileId.slice(0, 12)}...)
                    </div>
                  )}

                  <div className="text-xs text-gray-100 whitespace-pre-wrap leading-relaxed font-sans">
                    {text.trim() || 'Xabar matni bu yerda ko\'rinadi...'}
                  </div>

                  {buttons.length > 0 && (
                    <div className="space-y-1.5 pt-2">
                      {buttons.map((b, i) => (
                        <div
                          key={i}
                          className="bg-[#2b5278] hover:bg-[#32608c] text-white text-xs font-medium py-1.5 px-3 rounded-lg text-center truncate flex items-center justify-center gap-1 shadow-sm"
                        >
                          <span>{b.text || 'Tugma'}</span>
                          <ExternalLink className="w-3 h-3 opacity-60" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Progress & Live Results */}
              {status && (
                <div className="card space-y-4 border-indigo-200 dark:border-indigo-900/60">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 text-sm">
                      {status.done ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      )}
                      {status.done ? 'Yuborish yakunlandi!' : 'Xabarlar yuborilmoqda...'}
                    </h3>
                    <span className="text-xs text-gray-400 font-mono">#{broadcastId}</span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                      <p className="text-lg font-bold text-gray-900 dark:text-white">{status.total}</p>
                      <p className="text-[10px] text-gray-500">Jami</p>
                    </div>
                    <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <p className="text-lg font-bold text-green-600 dark:text-green-400">{status.sent}</p>
                      <p className="text-[10px] text-gray-500">Yetkazildi</p>
                    </div>
                    <div className="p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                      <p className="text-lg font-bold text-amber-600 dark:text-amber-400">{status.blocked || 0}</p>
                      <p className="text-[10px] text-gray-500">Bloklagan</p>
                    </div>
                    <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                      <p className="text-lg font-bold text-red-600 dark:text-red-400">{status.failed}</p>
                      <p className="text-[10px] text-gray-500">Xatolik</p>
                    </div>
                  </div>

                  {status.total > 0 && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Progress ({status.duration_seconds}s)</span>
                        <span>{Math.round((status.sent / status.total) * 100)}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                          style={{ width: `${(status.sent / status.total) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* SECTION 2: DOIMIY HOMIYLIK REKLAMASI (POST-DELIVERY ADS)         */}
        {/* ---------------------------------------------------------------- */}
        {activeTab === 'sponsor' && (
          <div className="card space-y-6 border-purple-200 dark:border-purple-900/40">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Tv className="w-5 h-5 text-purple-600" /> Kino va Serial ostidagi Doimiy Homiy
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Foydalanuvchi har safar botdan kino yoki serial qismini ko'rganda, video tagiga avtomatik qo'shiladigan reklama havolasi va matni.
                </p>
              </div>

              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold bg-purple-50 dark:bg-purple-950/40 px-3 py-1.5 rounded-lg border border-purple-200 dark:border-purple-800 self-start sm:self-auto">
                <span>Homiylikni yoqish:</span>
                <input
                  type="checkbox"
                  checked={sponsorSettings.sponsor_ad_enabled === 'true'}
                  onChange={(e) =>
                    setSponsorSettings({
                      ...sponsorSettings,
                      sponsor_ad_enabled: e.target.checked ? 'true' : 'false',
                    })
                  }
                  className="w-4 h-4 accent-purple-600 rounded"
                />
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                  Video ostidagi homiy matni (Sponsor Text)
                </label>
                <textarea
                  value={sponsorSettings.sponsor_ad_text}
                  onChange={(e) =>
                    setSponsorSettings({ ...sponsorSettings, sponsor_ad_text: e.target.value })
                  }
                  rows={3}
                  className="input font-mono text-xs leading-relaxed"
                  placeholder="📢 *Bosh homiyimiz:* @KinoKanal — Eng so'nggi premyeralar birinchi bo'lib shu yerda!"
                />
                <p className="text-[11px] text-gray-400">
                  Ushbu matn bot tomonidan yuboriladigan har bir kino va epizod videosi izohiga (caption) qo'shiladi.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                  Homiy tugmasi matni (Button text)
                </label>
                <input
                  value={sponsorSettings.sponsor_ad_button_text}
                  onChange={(e) =>
                    setSponsorSettings({
                      ...sponsorSettings,
                      sponsor_ad_button_text: e.target.value,
                    })
                  }
                  className="input text-xs"
                  placeholder="🔥 Homiy kanaliga obuna bo'lish"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">
                  Homiy havolasi (URL link)
                </label>
                <input
                  value={sponsorSettings.sponsor_ad_button_url}
                  onChange={(e) =>
                    setSponsorSettings({
                      ...sponsorSettings,
                      sponsor_ad_button_url: e.target.value,
                    })
                  }
                  className="input text-xs font-mono"
                  placeholder="https://t.me/kanal_nomi yoki https://homiy.uz"
                />
              </div>
            </div>

            {sponsorSaved && (
              <div className="p-3 bg-green-50 dark:bg-green-950/40 text-green-700 dark:text-green-300 text-xs rounded-lg font-medium border border-green-200 dark:border-green-800">
                ✓ Homiy sozlamalari muvaffaqiyatli saqlandi!
              </div>
            )}

            <div className="flex justify-end pt-3 border-t border-gray-100 dark:border-gray-800">
              <button
                type="button"
                onClick={() => saveSponsorMut.mutate(sponsorSettings)}
                disabled={saveSponsorMut.isPending}
                className="btn-primary flex items-center gap-2 text-xs py-2 px-5"
              >
                <Save className="w-4 h-4" />
                {saveSponsorMut.isPending ? 'Saqlanmoqda...' : 'Homiylik sozlamalarini saqlash'}
              </button>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
