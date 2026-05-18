from fastapi import APIRouter

from app.api.routes import chat, documents, eval, feedback, gift_list, health, images, products

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(gift_list.router, prefix="/gift-list", tags=["gift-list"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(eval.router, prefix="/eval", tags=["evaluation"])
