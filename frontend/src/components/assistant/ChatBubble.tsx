import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Leaf, Loader2, MessageCircle, Mic, MicOff, Send, X } from 'lucide-react';
import { apiAskAssistant } from '../../api/assistant';
import { useCrops } from '../../hooks/useCrops';
import { useSpeechRecognition, useSpeechSynthesis } from '../../hooks/useSpeech';
import type { CropCode } from '../../types';
import { ChatMessage, type ChatItem } from './ChatMessage';
import { OPEN_CHAT_EVENT, type ChatDiagnosisContext } from './chatEvents';

const SUGGESTIONS = ['Sầu riêng cháy mép lá?', 'Chôm chôm phấn trắng?', 'Thán thư măng cụt?'] as const;
const DIAGNOSIS_SUGGESTIONS = ['Xử lý thế nào?', 'Dùng thuốc gì?', 'Bao lâu thì khỏi?'] as const;

function errorText(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === 'string' ? detail : 'Chưa trả lời được. Thử lại sau.';
}

/** Floating assistant: a mint bubble on every page that opens a voice-enabled chat panel. */
export function ChatBubble() {
  const { crops, cropName } = useCrops();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<readonly ChatItem[]>([]);
  const [draft, setDraft] = useState('');
  const [crop, setCrop] = useState<CropCode | ''>('');
  const [asking, setAsking] = useState(false);
  const [context, setContext] = useState<ChatDiagnosisContext | null>(null);
  const nextId = useRef(1);
  const listRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const tts = useSpeechSynthesis();

  useEffect(() => {
    const onOpen = (event: Event) => {
      const detail = (event as CustomEvent<ChatDiagnosisContext | undefined>).detail;
      if (detail) setContext(detail);
      setOpen(true);
    };
    window.addEventListener(OPEN_CHAT_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_CHAT_EVENT, onOpen);
  }, []);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    } else {
      tts.cancel();
      // A diagnosis context belongs to one "Hỏi bác sĩ AI" session; reopening the bubble is a general chat.
      setContext(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [items, asking]);

  const push = (item: Omit<ChatItem, 'id'>) => {
    const id = nextId.current++;
    setItems((prev) => [...prev, { ...item, id }]);
  };

  const ask = async (text: string, byVoice = false) => {
    const q = text.trim();
    if (q.length < 2 || asking) return;
    setDraft('');
    tts.cancel();
    push({ role: 'user', text: q });
    setAsking(true);
    try {
      const res = await apiAskAssistant(q, crop || null, context?.diagnosisId);
      push({
        role: 'bot',
        text: res.answer,
        source: res.source,
        related: res.related.map((r) => `${r.class_name} (${cropName(r.crop_code)})`),
      });
      if (byVoice) tts.speak(res.answer);
    } catch (err: unknown) {
      push({ role: 'bot', text: errorText(err) });
    } finally {
      setAsking(false);
    }
  };

  const stt = useSpeechRecognition((text) => void ask(text, true));

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void ask(draft);
  };

  return (
    <>
      {open && (
        <section
          role="dialog"
          aria-label="Trợ lý LEAF"
          className="fixed z-50 inset-0 sm:inset-auto sm:bottom-24 sm:right-6 sm:w-[380px] sm:h-[560px] sm:max-h-[calc(100vh-8rem)] flex flex-col bg-paper sm:rounded-[20px] shadow-2xl border border-line overflow-hidden"
        >
          <header className="bg-forest text-white px-4 py-3 flex items-center gap-3 shrink-0">
            <span className="w-9 h-9 rounded-full bg-mint text-forest flex items-center justify-center shrink-0">
              <MessageCircle size={18} />
            </span>
            <p className="font-display font-bold flex-1">Trợ lý LEAF</p>
            <select
              aria-label="Loại cây"
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="bg-forest-2 text-white text-xs rounded-lg px-2 py-1.5 border border-white/15 outline-none"
            >
              <option value="">Mọi cây</option>
              {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
            </select>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Đóng trợ lý"
              className="w-8 h-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10 flex items-center justify-center cursor-pointer"
            >
              <X size={18} />
            </button>
          </header>

          {context && (
            <div className="px-4 py-2 bg-leaf-wash border-b border-line flex items-center gap-2 text-xs text-ink shrink-0">
              <Leaf size={14} className="text-leaf shrink-0" />
              <span className="truncate flex-1">
                Đang hỏi về: <b>{context.label}</b>
              </span>
              <button
                type="button"
                onClick={() => setContext(null)}
                aria-label="Bỏ ngữ cảnh chẩn đoán"
                className="w-6 h-6 rounded-md text-ink/50 hover:text-ink hover:bg-white flex items-center justify-center cursor-pointer"
              >
                <X size={14} />
              </button>
            </div>
          )}

          <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-3" aria-live="polite">
            {items.length === 0 ? (
              <div className="h-full flex flex-col justify-end gap-2">
                <p className="self-start max-w-[85%] rounded-2xl rounded-bl-md bg-white border border-line px-3.5 py-2.5 text-sm text-ink mb-auto">
                  Hỏi gì về bệnh cây? Gõ hoặc bấm micro để nói.
                </p>
                {(context ? DIAGNOSIS_SUGGESTIONS : SUGGESTIONS).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => void ask(s)}
                    className="self-end text-sm px-3.5 py-2 rounded-2xl rounded-br-md bg-white border border-line text-ink hover:border-leaf cursor-pointer"
                  >
                    {s}
                  </button>
                ))}
              </div>
            ) : (
              items.map((item) => (
                <ChatMessage
                  key={item.id}
                  item={item}
                  canSpeak={tts.supported}
                  speaking={tts.speaking}
                  onSpeak={tts.speak}
                  onStop={tts.cancel}
                />
              ))
            )}
            {asking && (
              <div className="flex justify-start">
                <span className="rounded-2xl rounded-bl-md bg-white border border-line px-3.5 py-2.5 text-ink/50">
                  <Loader2 size={16} className="animate-spin" />
                </span>
              </div>
            )}
          </div>

          {stt.listening && (
            <p className="px-4 pb-1 text-xs text-leaf truncate">{stt.interim || 'Đang nghe…'}</p>
          )}
          {stt.error && !stt.listening && <p className="px-4 pb-1 text-xs text-red-600 truncate">{stt.error}</p>}

          <form onSubmit={submit} className="p-3 border-t border-line bg-white flex items-center gap-2 shrink-0">
            {stt.supported && (
              <button
                type="button"
                onClick={stt.listening ? stt.stop : stt.start}
                disabled={asking}
                aria-pressed={stt.listening}
                aria-label={stt.listening ? 'Dừng nghe' : 'Nói câu hỏi'}
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 cursor-pointer disabled:opacity-50 ${
                  stt.listening ? 'bg-red-600 text-white animate-pulse' : 'bg-leaf-wash text-leaf hover:bg-mint-soft'
                }`}
              >
                {stt.listening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
            )}
            <label htmlFor="chat-input" className="sr-only">Câu hỏi</label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              maxLength={500}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Hỏi về bệnh cây…"
              className="flex-1 min-w-0 h-10 rounded-full bg-paper px-4 text-sm outline-none focus:ring-2 focus:ring-leaf/30"
            />
            <button
              type="submit"
              disabled={asking || draft.trim().length < 2}
              aria-label="Gửi"
              className="w-10 h-10 rounded-full bg-leaf text-white flex items-center justify-center shrink-0 hover:bg-leaf-dark disabled:opacity-40 cursor-pointer"
            >
              <Send size={17} />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? 'Đóng trợ lý' : 'Mở trợ lý'}
        aria-expanded={open}
        className={`fixed z-50 bottom-5 right-5 sm:bottom-6 sm:right-6 w-14 h-14 rounded-full bg-mint text-forest shadow-xl flex items-center justify-center hover:scale-105 transition-transform cursor-pointer ${
          open ? 'hidden sm:flex' : 'flex'
        }`}
      >
        {open ? <X size={24} /> : <MessageCircle size={26} />}
      </button>
    </>
  );
}
