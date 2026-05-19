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

export interface GiftListCheckoutItem {
  product: ProductCardData;
  quantity: number;
  subtotal?: string | number | null;
}

export interface GiftListCheckoutPreviewResponse {
  list_id: string;
  items: GiftListCheckoutItem[];
  total_count: number;
  total_amount?: string | number | null;
  unavailable_product_ids: string[];
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

export async function removeGiftListItem(productId: string, listId = 'default') {
  const response = await fetch(
    `${API_BASE}/gift-list/items/${encodeURIComponent(productId)}?list_id=${encodeURIComponent(listId)}`,
    { method: 'DELETE' },
  );

  if (!response.ok) {
    throw new Error(`Remove gift list item failed: ${response.status}`);
  }

  return response.json() as Promise<GiftListResponse>;
}

export async function updateGiftListItemQuantity(
  productId: string,
  quantity: number,
  listId = 'default',
) {
  const response = await fetch(
    `${API_BASE}/gift-list/items/${encodeURIComponent(productId)}`,
    {
      method: 'PATCH',
      headers: {
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        list_id: listId,
        quantity,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(`Update gift list item failed: ${response.status}`);
  }

  return response.json() as Promise<GiftListResponse>;
}

export async function previewGiftListCheckout(
  items: Array<{ product_id: string; quantity: number }>,
  listId = 'default',
) {
  const response = await fetch(`${API_BASE}/gift-list/checkout-preview`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      list_id: listId,
      items,
    }),
  });

  if (!response.ok) {
    throw new Error(`Preview gift list checkout failed: ${response.status}`);
  }

  return response.json() as Promise<GiftListCheckoutPreviewResponse>;
}
