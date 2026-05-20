export const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export type BudgetLevel = 'low' | 'mid' | 'high' | 'luxury';
export type GiftRole = 'main_gift' | 'addon_gift';

export interface ProductCardData {
  product_id: string;
  name: string;
  image_url?: string | null;
  price?: number | string | null;
  tags: string[];
  highlights: string[];
  reason: string;
  display_reason?: string | null;
  matched_features?: string[];
  penalties?: string[];
  detail_url?: string | null;
  scenarios?: string[];
  target_people?: string[];
  budget_level?: BudgetLevel | null;
  avoid_for?: string[];
  gift_role?: GiftRole | null;
}

export interface RelaxationOptionData {
  option_id: string;
  label: string;
  description: string;
  patch?: Record<string, unknown>;
}

export interface ChatRequest {
  user_id?: string | null;
  conversation_id?: string | null;
  message: string;
  image_ids: string[];
  recommendation_strategy?: 'llm_direct' | 'hybrid_algorithm' | 'llm_rerank' | null;
  allow_generic_recommendation?: boolean;
  use_profile?: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  products: ProductCardData[];
  citations: { document_id: string; chunk_id: string; text: string }[];
  needs_clarification?: boolean;
  clarification_question?: string | null;
  needs_relaxation?: boolean;
  relaxation_reason?: string | null;
  relaxation_options?: RelaxationOptionData[];
  suggested_questions?: string[];
}

export async function chat(payload: ChatRequest, signal?: AbortSignal) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Chat failed: ${response.status}`);
  }

  return response.json() as Promise<ChatResponse>;
}

export interface StreamEvent {
  event: 'message_delta' | 'product_cards' | 'relaxation_options' | 'citation' | 'done' | 'error';
  text?: string | null;
  products?: ProductCardData[];
  relaxation_options?: RelaxationOptionData[];
  relaxation_reason?: string | null;
  suggested_questions?: string[];
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
