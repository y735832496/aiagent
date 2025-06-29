from typing import Optional
from app.config import settings

class StorageFactory:
    """存储后端工厂类"""
    
    @staticmethod
    def create_storage():
        """根据配置创建存储后端实例"""
        backend = settings.document_backend.lower()
        
        # 优先使用FAISS存储
        if backend in ["faiss", "default"]:
            try:
                from .faiss_storage import FAISSStorage
                print("✅ 使用FAISS向量数据库")
                return FAISSStorage()
            except ImportError as e:
                print(f"❌ 无法导入FAISS存储后端: {e}")
                raise e
        
        # 其他数据库存储（暂时不支持）
        elif backend in ["mysql", "mongodb", "elasticsearch", "chroma"]:
            print(f"⚠️ {backend.upper()}存储后端暂不支持")
            print("🔄 使用FAISS向量数据库")
            try:
                from .faiss_storage import FAISSStorage
                print("✅ 使用FAISS向量数据库")
                return FAISSStorage()
            except ImportError as e:
                print(f"❌ 无法导入FAISS存储后端: {e}")
                raise e
        
        # 默认使用FAISS
        else:
            print(f"⚠️ 未知的存储后端: {backend}")
            print("🔄 使用FAISS向量数据库")
            try:
                from .faiss_storage import FAISSStorage
                print("✅ 使用FAISS向量数据库")
                return FAISSStorage()
            except ImportError as e:
                print(f"❌ 无法导入FAISS存储后端: {e}")
                raise e
    
    @staticmethod
    def get_available_backends() -> list:
        """获取可用的存储后端列表"""
        return [
            "faiss"
        ] 