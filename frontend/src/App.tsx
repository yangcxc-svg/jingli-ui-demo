import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import {
  ComboChatPage,
  CompareRecommendationPage,
  GiftCartPage,
  GiftComboPlanPage,
  GiftSolutionPage,
  HomePage,
  JingliPage,
  PremiumComboPlanPage,
} from './pages/AppPages';

function useMobileViewportHeight() {
  const getViewportHeight = () => Math.floor(window.visualViewport?.height ?? window.innerHeight);
  const [appHeight, setAppHeight] = useState(() => Math.min(844, getViewportHeight()));

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
    const syncHeight = () => setAppHeight(Math.min(844, getViewportHeight()));
    syncHeight();
    const timers = [80, 240, 600].map((delay) => window.setTimeout(syncHeight, delay));
    window.addEventListener('resize', syncHeight);
    window.visualViewport?.addEventListener('resize', syncHeight);
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      window.removeEventListener('resize', syncHeight);
      window.visualViewport?.removeEventListener('resize', syncHeight);
    };
  }, []);

  return appHeight;
}

export default function App() {
  const appHeight = useMobileViewportHeight();

  return (
    <main className="flex h-screen items-center justify-center overflow-hidden bg-[#f3f4f7] text-zinc-950">
      <section
        className="mx-auto w-[390px] overflow-hidden rounded-[34px] bg-gradient-to-b from-[#fff4f1] via-[#f6f3f2] to-[#f1f2f4] shadow-2xl ring-1 ring-black/5"
        style={{ height: appHeight }}
      >
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/jingli" element={<JingliPage />} />
            <Route path="/combo-chat" element={<ComboChatPage />} />
            <Route path="/compare" element={<CompareRecommendationPage />} />
            <Route path="/combo-plan" element={<GiftComboPlanPage />} />
            <Route path="/gift-solution" element={<GiftSolutionPage />} />
            <Route path="/combo-premium" element={<PremiumComboPlanPage />} />
            <Route path="/cart" element={<GiftCartPage />} />
            <Route path="/combo" element={<Navigate to="/combo-plan" replace />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </BrowserRouter>
      </section>
    </main>
  );
}
