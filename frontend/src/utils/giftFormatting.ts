import type { ProductCardData } from '../api/chat';
import type { GiftPlanResponse } from '../api/giftPlan';

export function formatProductPrice(price: ProductCardData['price']) {
  if (price === null || price === undefined || price === '') return '价格待确认';
  return typeof price === 'number' ? `¥${price}` : `¥${String(price).replace(/^¥/, '')}`;
}

export function toAmount(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') return 0;
  const parsed = Number(String(value).replace(/[^\d.]/g, ''));
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatAmount(value: number | string | null | undefined) {
  const amount = toAmount(value);
  return `¥${amount.toFixed(amount % 1 === 0 ? 0 : 2)}`;
}

export function mergeProducts(existing: ProductCardData[], incoming: ProductCardData[]) {
  const seen = new Set(existing.map((product) => product.product_id));
  return [
    ...existing,
    ...incoming.filter((product) => {
      if (seen.has(product.product_id)) return false;
      seen.add(product.product_id);
      return true;
    }),
  ];
}

export function saveGiftPlan(plan: GiftPlanResponse) {
  window.localStorage.setItem('jingli-current-gift-plan', JSON.stringify(plan));
}

export function loadGiftPlan() {
  const raw = window.localStorage.getItem('jingli-current-gift-plan');
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GiftPlanResponse;
  } catch {
    return null;
  }
}

