/**
 * v2 前端专用 API 客户端：
 * - getInstantProducts：取真实商品库（用于"现货尊享特区"展示）
 * - generateRecommendations：把 wizard 字段映射到后端 GiftSolutionGenerateRequest，并按单品/组合形态转成 v2 渲染结构
 */
import { API_BASE, type ProductCardData } from '../../api/chat';
import type { GiftPlanValuePoint } from '../../api/giftPlan';
import { generateGiftSolution, type GiftShapeDecisionData } from '../../api/giftSolution';

export interface V2InstantProduct {
  id: string;
  name: string;
  price: number;
  image: string;
  desc: string;
  tag: string;
}

export interface V2Recommendation {
  productId: string;
  name: string;
  price: number;
  rationale: string;
  tags: string[];
  imageUrl: string | null;
  scenarios: string[];
  targetPeople: string[];
  giftRole?: string | null;
}

export interface V2RecommendationResult {
  planId: string;
  title: string;
  answer: string;
  budget?: number | null;
  totalAmount: number;
  valuePoints: GiftPlanValuePoint[];
  recommendations: V2Recommendation[];
  shapeDecision?: GiftShapeDecisionData | null;
  solution?: {
    summary: string;
    recommendationReason: string;
    givingTiming: string;
    givingPlace: string;
    giftTalk: string;
    recipientReactionReply: string;
    packagingAdvice: string;
    avoidTips: string[];
    selectedPlanType?: string | null;
    planJudgeReason?: string | null;
  } | null;
}

export interface V2WizardInput {
  relation: string;
  age: string;
  occasion?: string;
  budget: number;
  tags: string[];
  background?: string;
}

const toNumber = (value: number | string | null | undefined): number => {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const buildMessage = ({ relation, age, occasion, budget, tags, background }: V2WizardInput): string => {
  const occasionPart = occasion?.trim() ? `送礼场合：${occasion.trim()}。` : '';
  const tagPart = tags.length > 0 ? `TA 的特质标签：${tags.join('、')}。` : '';
  const backgroundPart = background?.trim() ? `补充要求：${background.trim()}。` : '';
  return `想给${relation}（${age}）挑选一份心意礼物，预算约 ${budget} 元。${occasionPart}${tagPart}${backgroundPart}请推荐合适的方案。`;
};

const cardToRecommendation = (card: ProductCardData): V2Recommendation => ({
  productId: card.product_id,
  name: card.name,
  price: toNumber(card.price),
  rationale: card.display_reason || card.reason || card.highlights?.[0] || '匹配你当前的送礼需求',
  tags: (card.tags ?? []).slice(0, 3),
  imageUrl: card.image_url || null,
  scenarios: card.scenarios ?? [],
  targetPeople: card.target_people ?? [],
  giftRole: card.gift_role ?? null,
});

export async function generateRecommendations(input: V2WizardInput): Promise<V2RecommendationResult> {
  const data = await generateGiftSolution({
    message: buildMessage(input),
    recommendation_strategy: 'hybrid_algorithm',
    allow_generic_recommendation: true,
    use_profile: true,
  });
  return {
    planId: data.solution_id,
    title: data.title,
    answer: data.summary,
    budget: input.budget,
    totalAmount: toNumber(data.total_amount),
    valuePoints: [],
    recommendations: (data.products ?? []).map(cardToRecommendation),
    shapeDecision: data.shape_decision,
    solution: {
      summary: data.summary,
      recommendationReason: data.recommendation_reason,
      givingTiming: data.giving_timing,
      givingPlace: data.giving_place,
      giftTalk: data.gift_talk,
      recipientReactionReply: data.recipient_reaction_reply,
      packagingAdvice: data.packaging_advice,
      avoidTips: data.avoid_tips ?? [],
      selectedPlanType: data.selected_plan_type,
      planJudgeReason: data.plan_judge_reason,
    },
  };
}

export async function getInstantProducts(limit = 4): Promise<V2InstantProduct[]> {
  const response = await fetch(`${API_BASE}/products`);
  if (!response.ok) {
    throw new Error(`Fetch instant products failed: ${response.status}`);
  }
  const list = (await response.json()) as Array<{
    product_id: string;
    name: string;
    category?: string | null;
    price: number | string | null;
    image_url?: string | null;
    tags?: string[];
    highlights?: string[];
    scenarios?: string[];
    target_people?: string[];
  }>;
  const giftSignals = ['香', '礼', '茶', '花', '杯', '围巾', '健康', '家居', '咖啡', '美妆', '护肤', '首饰'];
  const scoreProduct = (p: (typeof list)[number]) => {
    const joined = [
      p.name,
      p.category,
      ...(p.tags ?? []),
      ...(p.highlights ?? []),
      ...(p.scenarios ?? []),
      ...(p.target_people ?? []),
    ].join(' ');
    const giftScore = giftSignals.reduce((score, signal) => score + (joined.includes(signal) ? 8 : 0), 0);
    const imageScore = p.image_url ? 20 : 0;
    const price = toNumber(p.price);
    const priceScore = price >= 80 && price <= 2500 ? 12 : price > 0 ? 4 : 0;
    return giftScore + imageScore + priceScore;
  };
  // 首页是品牌门面，优先展示有图、送礼感强的商品，而不是简单按价格取最贵。
  const sorted = [...list].sort((a, b) => scoreProduct(b) - scoreProduct(a));
  return sorted.slice(0, limit).map((p) => ({
    id: p.product_id,
    name: p.name,
    price: toNumber(p.price),
    image: p.image_url || '',
    desc: p.highlights?.[0] || '',
    tag: p.tags?.[0] || '精选',
  }));
}

export async function searchInstantProducts(query: string, limit = 20): Promise<V2InstantProduct[]> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });
  const response = await fetch(`${API_BASE}/products/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Search products failed: ${response.status}`);
  }
  const list = (await response.json()) as Array<{
    product_id: string;
    name: string;
    price: number | string | null;
    image_url?: string | null;
    tags?: string[];
    highlights?: string[];
  }>;
  return list.map((p) => ({
    id: p.product_id,
    name: p.name,
    price: toNumber(p.price),
    image: p.image_url || '',
    desc: p.highlights?.[0] || '',
    tag: p.tags?.[0] || '搜索结果',
  }));
}
