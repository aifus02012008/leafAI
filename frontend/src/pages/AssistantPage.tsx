import { useState, type FormEvent } from 'react';
import { Bot, Loader2, Mic, MicOff, Send, Square, Volume2 } from 'lucide-react';
import { apiAskAssistant } from '../api/assistant';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import { useSpeechRecognition, useSpeechSynthesis } from '../hooks/useSpeech';
import type { AssistantAnswer, CropCode } from '../types';

const SUGGESTIONS = [
  'Lá sầu riêng bị cháy từ mép, phải làm sao?',
  'Lá chôm chôm có lớp phấn trắng là bệnh gì?',
  'Phòng bệnh thán thư cho măng cụt thế nào?',
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
    <div className="space-y-6 max-w-3xl">
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Hỏi Đáp <span className="text-gradient">Bằng Giọng Nói</span>
        </h1>
        <p className="text-sm text-slate-600">Bấm vào micro và nói câu hỏi về bệnh cây. LEAF AI sẽ trả lời và đọc to cho bạn nghe.</p>
      </div>

      <div className="clean-card p-6 rounded-3xl flex flex-col items-center gap-4 text-center">
        {stt.supported ? (
          <button
            type="button"
            onClick={stt.listening ? stt.stop : stt.start}
            disabled={asking}
            aria-pressed={stt.listening}
            aria-label={stt.listening ? 'Dừng ghi âm' : 'Bấm để nói câu hỏi'}
            className={`w-28 h-28 rounded-full flex items-center justify-center text-white shadow-lg transition-all ${
              stt.listening ? 'bg-red-600 animate-pulse' : 'bg-[#15803D] hover:scale-105'
            } disabled:opacity-60`}
          >
            {stt.listening ? <MicOff size={44} /> : <Mic size={44} />}
          </button>
        ) : (
          <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-2xl p-3">
            Trình duyệt này chưa hỗ trợ nhận giọng nói. Hãy dùng Chrome trên điện thoại Android hoặc máy tính, hoặc gõ câu hỏi bên dưới.
          </p>
        )}
        <p className="text-base font-semibold text-slate-800 min-h-6" aria-live="polite">
          {stt.listening ? (stt.interim || 'Đang nghe…') : stt.error ?? (stt.supported ? 'Bấm micro rồi nói' : '')}
        </p>
      </div>

      <form onSubmit={submit} className="clean-card p-5 rounded-3xl space-y-3">
        <label htmlFor="assistant-q" className="block text-sm font-bold text-slate-700">Câu hỏi (có thể sửa lại trước khi gửi)</label>
        <textarea
          id="assistant-q"
          rows={3}
          maxLength={500}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="input-clean text-base"
          placeholder="Ví dụ: lá sầu riêng bị cháy từ mép phải làm sao?"
        />
        <div className="flex flex-wrap items-center gap-2">
          <select aria-label="Loại cây" value={crop} onChange={(e) => setCrop(e.target.value)} className="input-clean py-2 text-sm w-auto">
            <option value="">Mọi loại cây</option>
            {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
          </select>
          <button type="submit" disabled={asking || question.trim().length < 2} className="btn-primary text-sm py-2.5 px-5">
            {asking ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span>Gửi câu hỏi</span>
          </button>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          {SUGGESTIONS.map((s) => (
            <button key={s} type="button" onClick={() => { setQuestion(s); void ask(s); }} className="text-xs px-3 py-1.5 rounded-full bg-white border border-[#E2EFE7] hover:border-emerald-300">
              {s}
            </button>
          ))}
        </div>
      </form>

      {answer && (
        <section aria-live="polite" className="clean-card p-5 sm:p-6 rounded-3xl space-y-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
              <Bot size={15} /> Trả lời {answer.source === 'ai' ? '(AI)' : '(từ thư viện bệnh)'}
            </span>
            {tts.supported && (
              <button type="button" onClick={() => (tts.speaking ? tts.cancel() : tts.speak(answer.answer))} className="btn-secondary text-sm py-2 px-3.5">
                {tts.speaking ? <Square size={15} /> : <Volume2 size={15} />}
                <span>{tts.speaking ? 'Dừng đọc' : 'Đọc lại'}</span>
              </button>
            )}
          </div>
          <p className="text-base leading-relaxed text-slate-800 whitespace-pre-line">{answer.answer}</p>
          {tts.supported && !tts.hasVietnameseVoice && (
            <p className="text-[11px] text-slate-500">Máy chưa có giọng đọc tiếng Việt; có thể cài thêm trong phần Cài đặt › Ngôn ngữ của điện thoại.</p>
          )}
          {answer.related.length > 0 && (
            <p className="text-xs text-slate-500">
              Liên quan: {answer.related.map((r) => `${r.class_name} (${cropName(r.crop_code)})`).join(' · ')}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
