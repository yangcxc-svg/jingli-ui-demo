import { API_BASE, type ProductCardData } from './chat';

export interface GiftListItem {
  product: ProductCardData;
  quantity: number;
  added_at: string;
}

export interface GiftListResponse {
  list_id: string;
  items: GiftListItem[];
  total_count: number;
  total_amount?: string | number | null;
}

export async function addGiftListItem(product: ProductCardData, listId = 'default') {
  const response = await fetch(`${API_BASE}/gift-list/items`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      list_id: listId,
      product,
      quantity: 1,
    }),
  });

  if (!response.ok) {
    throw new Error(`Add gift list item failed: ${response.status}`);
  }

  return response.json() as Promise<GiftListResponse>;
}

export async function getGiftList(listId = 'default') {
  const response = await fetch(`${API_BASE}/gift-list?list_id=${encodeURIComponent(listId)}`);

  if (!response.ok) {
    throw new Error(`Get gift list failed: ${response.status}`);
  }

  return response.json() as Promise<GiftListResponse>;
}
