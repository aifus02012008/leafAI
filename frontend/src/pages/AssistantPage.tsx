import { useState, type FormEvent } from 'react';
import { Bot, Loader2, Mic, MicOff, Send, Square, Volume2 } from 'lucide-react';
import { apiAskAssistant } from '../api/assistant';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import { useSpeechRecognition, useSpeechSynthesis } from '../hooks/useSpeech';
import type { AssistantAnswer, CropCode } from '../types';

const SUGGESTIONS = [
  'Sầu riêng cháy mép lá?',
  'Chôm chôm phấn trắng?',
  'Thán thư măng cụt?',
];

export function AssistantPage() {
  const { crops, cropName } = useCrops();
  const [question, setQuestion] = useState('');
  const [crop, setCrop] = useState<CropCode | ''>('');
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [asking, setAsking] = useState(false);
  const tts = useSpeechSynthesis();

  const ask = async (text: string) => {
    const q = text.trim();
    if (q.length < 2) return;
    setAsking(true);
    tts.cancel();
    try {
      const res = await apiAskAssistant(q, crop || null);
      setAnswer(res);
      tts.speak(res.answer);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      showToast('error', typeof detail === 'string' ? detail : 'Trợ lý chưa trả lời được, vui lòng thử lại.');
    } finally {
      setAsking(false);
    }
  };

  const stt = useSpeechRecognition((text) => {
    setQuestion(text);
    void ask(text);
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void ask(question);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-5 space-y-6">
      <div className="clean-card p-5 flex flex-col items-center gap-4 text-center">
        {stt.supported ? (
          <button
            type="button"
            onClick={stt.listening ? stt.stop : stt.start}
            disabled={asking}
            aria-pressed={stt.listening}
            aria-label={stt.listening ? 'Dừng ghi âm' : 'Bấm để nói câu hỏi'}
            className={`w-28 h-28 rounded-full flex items-center justify-center text-white shadow-lg transition-all ${
              stt.listening ? 'bg-red-600 animate-pulse' : 'bg-[#1F7A4D] hover:scale-105'
            } disabled:opacity-60`}
          >
            {stt.listening ? <MicOff size={44} /> : <Mic size={44} />}
          </button>
        ) : (
          <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-2xl p-3">
            Máy chưa hỗ trợ giọng nói. Hãy gõ câu hỏi.
          </p>
        )}
        <p className="text-base font-semibold text-slate-800 min-h-6" aria-live="polite">
          {stt.listening ? (stt.interim || 'Đang nghe…') : stt.error ?? (stt.supported ? 'Bấm để nói' : '')}
        </p>
      </div>

      <form onSubmit={submit} className="clean-card p-5 space-y-3">
        <label htmlFor="assistant-q" className="sr-only">Câu hỏi</label>
        <textarea
          id="assistant-q"
          rows={3}
          maxLength={500}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="input-clean text-base"
          placeholder="Lá sầu riêng cháy mép?"
        />
        <div className="flex flex-wrap items-center gap-2">
          <select aria-label="Loại cây" value={crop} onChange={(e) => setCrop(e.target.value)} className="input-clean py-2 text-sm w-auto">
            <option value="">Mọi cây</option>
            {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
          </select>
          <button type="submit" disabled={asking || question.trim().length < 2} className="btn-primary text-sm py-2.5 px-5">
            {asking ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span>Gửi</span>
          </button>
        </div>
      </form>
      </div>

      <div className="lg:col-span-7">
      {answer ? (
        <section aria-live="polite" className="clean-card p-5 space-y-3 h-full">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
              <Bot size={15} /> {answer.source === 'ai' ? 'AI' : 'Thư viện'}
            </span>
            {tts.supported && (
              <button type="button" onClick={() => (tts.speaking ? tts.cancel() : tts.speak(answer.answer))} className="btn-secondary text-sm py-2 px-3.5">
                {tts.speaking ? <Square size={15} /> : <Volume2 size={15} />}
                <span>{tts.speaking ? 'Dừng' : 'Nghe'}</span>
              </button>
            )}
          </div>
          <p className="text-base leading-relaxed text-slate-800 whitespace-pre-line">{answer.answer}</p>
          {answer.related.length > 0 && (
            <p className="text-xs text-slate-500">
              {answer.related.map((r) => `${r.class_name} (${cropName(r.crop_code)})`).join(' · ')}
            </p>
          )}
        </section>
      ) : (
        <section aria-label="Câu hỏi gợi ý" className="clean-card p-5 space-y-3 h-full">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
            <Bot size={15} /> Hỏi thử
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                disabled={asking}
                onClick={() => { setQuestion(s); void ask(s); }}
                className="text-left text-sm font-medium px-4 py-3 rounded-xl bg-paper hover:bg-leaf-wash border border-transparent hover:border-[#1F7A4D]/30 transition-colors cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </section>
      )}
      </div>
    </div>
  );
}
