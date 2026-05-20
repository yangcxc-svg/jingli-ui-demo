import { useState } from 'react';
import { streamChat, type ProductCardData, type RelaxationOptionData } from '../api/chat';
import { mergeProducts } from '../utils/giftFormatting';

export type GiftRequestSource = 'input' | 'scene' | 'quick_question';

export interface GiftRequest {
  source: GiftRequestSource;
  displayMessage: string;
  requestMessage: string;
  sceneId?: string;
}

export type JingliChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  products?: ProductCardData[];
  relaxationOptions?: RelaxationOptionData[];
  relaxationReason?: string | null;
  suggestedQuestions?: string[];
};

const initialJingliMessages: JingliChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content: '你好，我是京礼。你可以告诉我：送给谁、什么场景、预算多少，我会帮你推荐更合适的礼物。',
  },
];

export function useGiftChat() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<JingliChatMessage[]>(initialJingliMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeRequest, setActiveRequest] = useState<GiftRequest | null>(null);
  const [lastRequest, setLastRequest] = useState<GiftRequest | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function sendGiftRequest(request: GiftRequest) {
    const requestMessage = request.requestMessage.trim();
    const displayMessage = request.displayMessage.trim() || requestMessage;
    if (!requestMessage || isStreaming) return false;

    const assistantId = crypto.randomUUID();
    setLastRequest(request);
    setErrorMessage(null);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: 'user', content: displayMessage },
      { id: assistantId, role: 'assistant', content: '', products: [] },
    ]);
    setIsStreaming(true);
    setActiveRequest(request);

    try {
      await streamChat(
        {
          conversation_id: conversationId,
          message: requestMessage,
          image_ids: [],
          recommendation_strategy: 'hybrid_algorithm',
        },
        (event) => {
          if (event.event === 'message_delta' && event.text) {
            setMessages((current) =>
              current.map((item) => (item.id === assistantId ? { ...item, content: item.content + event.text } : item)),
            );
          }
          if (event.event === 'product_cards' && event.products?.length) {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, products: mergeProducts(item.products ?? [], event.products ?? []) }
                  : item,
              ),
            );
          }
          if (event.event === 'relaxation_options') {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      relaxationOptions: event.relaxation_options ?? [],
                      relaxationReason: event.relaxation_reason ?? null,
                      suggestedQuestions: event.suggested_questions ?? [],
                    }
                  : item,
              ),
            );
          }
          if (event.event === 'error') {
            setErrorMessage(event.text || '后端返回了错误，请稍后重试。');
          }
          if (event.event === 'done' && event.conversation_id) {
            setConversationId(event.conversation_id);
          }
        },
      );
      return true;
    } catch (error) {
      console.error(error);
      setErrorMessage('后端暂时没有响应，请确认后端已启动在 8000 端口。');
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId && !item.content
            ? { ...item, content: '我这边连接后端失败了，请稍后再试。' }
            : item,
        ),
      );
      return false;
    } finally {
      setIsStreaming(false);
      setActiveRequest(null);
    }
  }

  async function retryLastRequest() {
    if (!lastRequest) return false;
    return sendGiftRequest(lastRequest);
  }

  return {
    activeRequest,
    errorMessage,
    isStreaming,
    lastRequest,
    messages,
    retryLastRequest,
    sendGiftRequest,
  };
}
