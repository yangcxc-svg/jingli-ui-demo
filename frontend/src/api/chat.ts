export const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export type BudgetLevel = 'low' | 'mid' | 'high' | 'luxury';

export interface ProductCardData {
  product_id: string;
  name: string;
  image_url?: string | null;
  price?: number | string | null;
  tags: string[];
  highlights: string[];
  reason: string;
  detail_url?: string | null;
  scenarios?: string[];
  target_people?: string[];
  budget_level?: BudgetLevel | null;
  avoid_for?: string[];
}

export interface ChatRequest {
  conversation_id?: string | null;
  message: string;
  image_ids: string[];
}

export interface StreamEvent {
  event: 'message_delta' | 'product_cards' | 'citation' | 'done' | 'error';
  text?: string | null;
  products?: ProductCardData[];
  conversation_id?: string | null;
  message_id?: string | null;
}

export async function streamChat(
  payload: ChatRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
) {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frame of frames) {
      const dataLine = frame.split('\n').find((line) => line.startsWith('data: '));
      if (!dataLine) continue;
      onEvent(JSON.parse(dataLine.slice(6)) as StreamEvent);
    }
  }
}
