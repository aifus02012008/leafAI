import { Square, Volume2 } from 'lucide-react';

export interface ChatItem {
  id: number;
  role: 'user' | 'bot';
  text: string;
  source?: 'ai' | 'library';
  related?: string[];
}

interface ChatMessageProps {
  item: ChatItem;
  canSpeak: boolean;
  speaking: boolean;
  onSpeak: (text: string) => void;
  onStop: () => void;
}

/** One chat bubble: farmer on the right (forest), assistant on the left (white, with a listen button). */
export function ChatMessage({ item, canSpeak, speaking, onSpeak, onStop }: ChatMessageProps) {
  if (item.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[80%] rounded-2xl rounded-br-md bg-forest text-white px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-line">
          {item.text}
        </p>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-1.5">
        <p className="rounded-2xl rounded-bl-md bg-white border border-line px-3.5 py-2.5 text-sm leading-relaxed text-ink whitespace-pre-line">
          {item.text}
        </p>
        <div className="flex items-center gap-2 pl-1 text-[11px] text-ink/45">
          {item.source && <span className="shrink-0 whitespace-nowrap">{item.source === 'ai' ? 'AI' : 'Thư viện'}</span>}
          {item.related && item.related.length > 0 && <span className="truncate min-w-0">· {item.related.join(', ')}</span>}
          {canSpeak && (
            <button
              type="button"
              onClick={() => (speaking ? onStop() : onSpeak(item.text))}
              className="ml-auto shrink-0 inline-flex items-center gap-1 font-semibold text-leaf hover:text-leaf-dark cursor-pointer"
              aria-label={speaking ? 'Dừng đọc' : 'Nghe câu trả lời'}
            >
              {speaking ? <Square size={12} /> : <Volume2 size={13} />}
              {speaking ? 'Dừng' : 'Nghe'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
