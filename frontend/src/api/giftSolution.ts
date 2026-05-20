import { API_BASE, type ProductCardData } from './chat';

export type GiftShape = 'single_gift' | 'gift_combo' | 'either';

export interface GiftShapeDecisionData {
  shape: GiftShape;
  confidence: number;
  reason: string;
  signals: string[];
  recommended_product_count: number;
  use_combo_optimizer: boolean;
}

export interface GiftSolutionResponse {
  solution_id: string;
  shape_decision: GiftShapeDecisionData;
  title: string;
  summary: string;
  products: ProductCardData[];
  total_amount?: number | string | null;
  recommendation_reason: string;
  giving_timing: string;
  giving_place: string;
  gift_talk: string;
  recipient_reaction_reply: string;
  packaging_advice: string;
  avoid_tips: string[];
  follow_up_question?: string | null;
  selected_plan_type?: string | null;
  plan_judge_reason?: string | null;
}

export async function generateGiftSolution(payload: {
  message: string;
  conversation_id?: string | null;
  user_id?: string | null;
  recommendation_strategy?: 'llm_direct' | 'hybrid_algorithm' | 'llm_rerank' | null;
  allow_generic_recommendation?: boolean;
  use_profile?: boolean;
}) {
  const response = await fetch(`${API_BASE}/gift-solution/generate`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Generate gift solution failed: ${response.status}`);
  }

  return response.json() as Promise<GiftSolutionResponse>;
}
