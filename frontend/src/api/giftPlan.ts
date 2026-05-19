import { API_BASE, type ProductCardData } from './chat';

export interface GiftPlanValuePoint {
  title: string;
  desc: string;
  icon: string;
}

export interface GiftPlanResponse {
  plan_id: string;
  title: string;
  requirement: string;
  strategy: string;
  budget?: string | number | null;
  total_amount: string | number;
  remaining_amount?: string | number | null;
  usage_percent?: number | null;
  answer: string;
  products: ProductCardData[];
  value_points: GiftPlanValuePoint[];
  replacement_chips: string[];
}

export async function generateGiftPlan(payload: {
  message: string;
  budget?: number | string | null;
  preference?: string | null;
}) {
  const response = await fetch(`${API_BASE}/gift-plan/generate`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Generate gift plan failed: ${response.status}`);
  }

  return response.json() as Promise<GiftPlanResponse>;
}
