/**
 * v2 内联 SVG 图标集（精简版 lucide）。
 * 不引入 lucide-react 依赖，按需扩展。
 */
import type { CSSProperties, FC, ReactElement } from 'react';

export type IconName =
  | 'sparkles'
  | 'arrow-right'
  | 'gift'
  | 'shopping-cart'
  | 'shopping-bag'
  | 'chevron-left'
  | 'cpu'
  | 'image'
  | 'info'
  | 'home'
  | 'truck'
  | 'check'
  | 'map-pin'
  | 'box'
  | 'qr-code'
  | 'credit-card'
  | 'mic'
  | 'x'
  | 'plus'
  | 'minus'
  | 'message-circle'
  | 'clock'
  | 'heart';

interface IconProps {
  name: IconName;
  className?: string;
  style?: CSSProperties;
}

const paths: Record<IconName, ReactElement> = {
  sparkles: (
    <>
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1" />
    </>
  ),
  'arrow-right': (
    <>
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </>
  ),
  gift: (
    <>
      <path d="M20 12v9H4v-9" />
      <path d="M2 7h20v5H2z" />
      <path d="M12 22V7" />
      <path d="M12 7a3 3 0 1 1-3-3c1.5 0 3 1.5 3 3z" />
      <path d="M12 7a3 3 0 1 0 3-3c-1.5 0-3 1.5-3 3z" />
    </>
  ),
  'shopping-cart': (
    <>
      <circle cx="9" cy="20" r="1.5" />
      <circle cx="18" cy="20" r="1.5" />
      <path d="M3 4h2l2.7 12.3a1 1 0 0 0 1 .7H18a1 1 0 0 0 1-.8L21 8H6" />
    </>
  ),
  'shopping-bag': (
    <>
      <path d="M6 2l-2 5v15h16V7l-2-5z" />
      <path d="M3 7h18" />
      <path d="M16 11a4 4 0 0 1-8 0" />
    </>
  ),
  'chevron-left': (
    <>
      <path d="M15 6l-6 6 6 6" />
    </>
  ),
  cpu: (
    <>
      <rect x="5" y="5" width="14" height="14" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" />
    </>
  ),
  image: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="M21 15l-5-5L5 21" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v.01M12 11v5" />
    </>
  ),
  home: (
    <>
      <path d="M3 11l9-7 9 7v9a2 2 0 0 1-2 2h-4v-6H9v6H5a2 2 0 0 1-2-2z" />
    </>
  ),
  truck: (
    <>
      <path d="M3 17V6h11v11" />
      <path d="M14 9h4l3 4v4h-7" />
      <circle cx="7" cy="18" r="1.8" />
      <circle cx="17" cy="18" r="1.8" />
    </>
  ),
  check: (
    <>
      <path d="M5 12l5 5L20 7" />
    </>
  ),
  'map-pin': (
    <>
      <path d="M12 22s7-7 7-13a7 7 0 1 0-14 0c0 6 7 13 7 13z" />
      <circle cx="12" cy="9" r="2.5" />
    </>
  ),
  box: (
    <>
      <path d="M21 16V8l-9-5-9 5v8l9 5 9-5z" />
      <path d="M3 8l9 5 9-5" />
      <path d="M12 22V13" />
    </>
  ),
  'qr-code': (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <path d="M14 14h3v3M20 14v3M14 20h7" />
    </>
  ),
  'credit-card': (
    <>
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M2 10h20" />
    </>
  ),
  mic: (
    <>
      <rect x="9" y="3" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </>
  ),
  x: (
    <>
      <path d="M6 6l12 12M18 6L6 18" />
    </>
  ),
  plus: (
    <>
      <path d="M12 5v14M5 12h14" />
    </>
  ),
  minus: (
    <>
      <path d="M5 12h14" />
    </>
  ),
  'message-circle': (
    <>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5a8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </>
  ),
  heart: (
    <>
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </>
  ),
};

export const Icon: FC<IconProps> = ({ name, className, style }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={style}
    aria-hidden
  >
    {paths[name]}
  </svg>
);