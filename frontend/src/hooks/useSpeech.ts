import { useCallback, useEffect, useRef, useState } from 'react';

/* Minimal typings: the Web Speech recognition API is not in TypeScript's DOM lib. */
interface RecognitionResultEvent {
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>;
}
interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((e: RecognitionResultEvent) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
}
type RecognitionCtor = new () => Recognition;

function getRecognitionCtor(): RecognitionCtor | null {
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

const ERROR_MESSAGES: Record<string, string> = {
  'not-allowed': 'Bạn chưa cho phép dùng micro. Hãy bật quyền micro cho trang web.',
  'no-speech': 'Không nghe thấy giọng nói. Bấm micro và nói lại nhé.',
  network: 'Nhận dạng giọng nói cần kết nối mạng.',
};

/** Vietnamese speech-to-text via the browser (Chrome/Edge/Android). */
export function useSpeechRecognition(onFinal: (text: string) => void) {
  const supported = typeof window !== 'undefined' && getRecognitionCtor() !== null;
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const onFinalRef = useRef(onFinal);
  onFinalRef.current = onFinal;

  const start = useCallback(() => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) return;
    recRef.current?.abort(); // a stale recognizer must not flip state for the new one
    const rec = new Ctor();
    rec.lang = 'vi-VN';
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (e) => {
      if (recRef.current !== rec) return;
      let finalText = '';
      let partial = '';
      for (let i = 0; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript;
        else partial += r[0].transcript;
      }
      setInterim(partial);
      if (finalText.trim()) onFinalRef.current(finalText.trim());
    };
    rec.onerror = (e) => {
      if (recRef.current !== rec || e.error === 'aborted') return;
      setError(ERROR_MESSAGES[e.error] ?? 'Không nhận dạng được giọng nói.');
    };
    rec.onend = () => {
      if (recRef.current !== rec) return;
      setListening(false);
      setInterim('');
    };
    setError(null);
    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
    } catch {
      recRef.current = null;
      setError('Không bật được micro. Vui lòng thử lại.');
    }
  }, []);

  const stop = useCallback(() => recRef.current?.stop(), []);

  useEffect(() => () => recRef.current?.abort(), []);

  return { supported, listening, interim, error, start, stop };
}

/** Vietnamese text-to-speech via the browser's speechSynthesis. */
export function useSpeechSynthesis() {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const [speaking, setSpeaking] = useState(false);
  const [hasVietnameseVoice, setHasVietnameseVoice] = useState(false);

  useEffect(() => {
    if (!supported) return;
    const update = () => setHasVietnameseVoice(window.speechSynthesis.getVoices().some((v) => v.lang.toLowerCase().startsWith('vi')));
    update();
    window.speechSynthesis.addEventListener('voiceschanged', update);
    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', update);
      window.speechSynthesis.cancel();
    };
  }, [supported]);

  const speak = useCallback(
    (text: string) => {
      if (!supported || !text) return;
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'vi-VN';
      utter.rate = 0.9; // slightly slower for older listeners
      const voice = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith('vi'));
      if (voice) utter.voice = voice;
      utter.onend = () => setSpeaking(false);
      utter.onerror = () => setSpeaking(false);
      setSpeaking(true);
      window.speechSynthesis.speak(utter);
    },
    [supported]
  );

  const cancel = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  return { supported, speaking, hasVietnameseVoice, speak, cancel };
}
