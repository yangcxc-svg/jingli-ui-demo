/**
 * v2 全局上下文：托管 wizard 表单、推荐结果、购物车快照、订单、灵动岛/Toast 与全局 loading。
 * 跨 /v2/home /v2/wizard /v2/recommendations /v2/cart /v2/checkout /v2/order-success 共享。
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import type { V2RecommendationResult } from '../api/v2Api';

export interface V2WizardState {
  relation: string;
  age: string;
  budget: number;
  tags: string[];
  background: string;
}

export interface V2CartItem {
  productId: string;
  name: string;
  price: number;
  imageUrl: string | null;
  desc: string;
  isAiCustom?: boolean;
}

export interface V2Address {
  recipient: string;
  phone: string;
  fullAddress: string;
}

export interface V2Order {
  orderId: string;
  paidAt: string;
  items: V2CartItem[];
  subtotal: number;
  packagingFee: number;
  shippingFee: number;
  totalAmount: number;
  needLuxuryBox: boolean;
  needAudioQR: boolean;
  address: V2Address;
}

interface IslandMessage {
  title: string;
  subtitle: string;
}

interface V2ContextValue {
  wizard: V2WizardState;
  setWizard: (next: Partial<V2WizardState>) => void;
  toggleTag: (tag: string) => void;

  recommendations: V2RecommendationResult | null;
  setRecommendations: (next: V2RecommendationResult | null) => void;

  // 本地购物车快照（与后端礼单 list_id="default" 同步）
  cartItems: V2CartItem[];
  setCartItems: (next: V2CartItem[]) => void;
  clearCart: () => void;

  // 结账偏好
  needLuxuryBox: boolean;
  setNeedLuxuryBox: (next: boolean) => void;
  needAudioQR: boolean;
  setNeedAudioQR: (next: boolean) => void;
  address: V2Address;

  // 订单
  latestOrder: V2Order | null;
  placeOrder: (params: { items: V2CartItem[]; subtotal: number }) => V2Order;

  loading: boolean;
  setLoading: (next: boolean) => void;

  island: IslandMessage | null;
  triggerIsland: (title: string, subtitle: string, ms?: number) => void;

  toast: string | null;
  showToast: (message: string, ms?: number) => void;
}

const V2Context = createContext<V2ContextValue | null>(null);

const DEFAULT_WIZARD: V2WizardState = {
  relation: '恋人',
  age: '20-30岁',
  budget: 600,
  tags: [],
  background: '',
};

const DEFAULT_ADDRESS: V2Address = {
  recipient: '李华',
  phone: '138****9988',
  fullAddress: '浙江省杭州市西湖区文三路古荡科技园 A座3楼',
};

const LUXURY_BOX_FEE = 68;

export function V2Provider({ children }: { children: ReactNode }) {
  const [wizard, setWizardRaw] = useState<V2WizardState>(DEFAULT_WIZARD);
  const [recommendations, setRecommendations] = useState<V2RecommendationResult | null>(null);
  const [cartItems, setCartItems] = useState<V2CartItem[]>([]);
  const [needLuxuryBox, setNeedLuxuryBox] = useState(true);
  const [needAudioQR, setNeedAudioQR] = useState(true);
  const [latestOrder, setLatestOrder] = useState<V2Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [island, setIsland] = useState<IslandMessage | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const setWizard = useCallback((next: Partial<V2WizardState>) => {
    setWizardRaw((prev) => ({ ...prev, ...next }));
  }, []);

  const toggleTag = useCallback((tag: string) => {
    setWizardRaw((prev) =>
      prev.tags.includes(tag)
        ? { ...prev, tags: prev.tags.filter((t) => t !== tag) }
        : { ...prev, tags: [...prev.tags, tag].slice(0, 3) },
    );
  }, []);

  const clearCart = useCallback(() => setCartItems([]), []);

  const triggerIsland = useCallback((title: string, subtitle: string, ms = 4000) => {
    setIsland({ title, subtitle });
    window.setTimeout(() => setIsland(null), ms);
  }, []);

  const showToast = useCallback((message: string, ms = 3000) => {
    setToast(message);
    window.setTimeout(() => setToast(null), ms);
  }, []);

  const placeOrder = useCallback<V2ContextValue['placeOrder']>(
    ({ items, subtotal }) => {
      const packagingFee = needLuxuryBox ? LUXURY_BOX_FEE : 0;
      const order: V2Order = {
        orderId: `JL${Date.now().toString().slice(-10)}`,
        paidAt: new Date().toISOString(),
        items,
        subtotal,
        packagingFee,
        shippingFee: 0,
        totalAmount: subtotal + packagingFee,
        needLuxuryBox,
        needAudioQR,
        address: DEFAULT_ADDRESS,
      };
      setLatestOrder(order);
      return order;
    },
    [needLuxuryBox, needAudioQR],
  );

  const value = useMemo<V2ContextValue>(
    () => ({
      wizard,
      setWizard,
      toggleTag,
      recommendations,
      setRecommendations,
      cartItems,
      setCartItems,
      clearCart,
      needLuxuryBox,
      setNeedLuxuryBox,
      needAudioQR,
      setNeedAudioQR,
      address: DEFAULT_ADDRESS,
      latestOrder,
      placeOrder,
      loading,
      setLoading,
      island,
      triggerIsland,
      toast,
      showToast,
    }),
    [
      wizard,
      setWizard,
      toggleTag,
      recommendations,
      cartItems,
      clearCart,
      needLuxuryBox,
      needAudioQR,
      latestOrder,
      placeOrder,
      loading,
      island,
      triggerIsland,
      toast,
      showToast,
    ],
  );

  return <V2Context.Provider value={value}>{children}</V2Context.Provider>;
}

export function useV2() {
  const ctx = useContext(V2Context);
  if (!ctx) {
    throw new Error('useV2 must be used within <V2Provider>');
  }
  return ctx;
}
