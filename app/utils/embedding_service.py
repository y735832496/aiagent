import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from app.config import settings

class EmbeddingService:
    """向量化服务"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载向量化模型"""
        try:
            print(f"正在加载向量化模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ 成功加载向量化模型: {self.model_name}")
            # 自动打印实际模型名和维度
            print(f"[DEBUG] 实际加载模型: {getattr(self.model, 'name_or_path', 'unknown')}, 维度: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            print(f"❌ 加载模型 {self.model_name} 失败: {e}")
            # 使用默认模型作为备选
            try:
                print("🔄 尝试加载备选模型: all-MiniLM-L6-v2")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.model_name = 'all-MiniLM-L6-v2'
                print("✅ 成功加载备选模型")
            except Exception as e2:
                print(f"❌ 备选模型也加载失败: {e2}")
                raise RuntimeError(f"无法加载任何向量化模型: {e2}")
    
    def encode_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """编码文本为向量"""
        if not self.model:
            raise RuntimeError("向量化模型未加载")
        
        try:
            embeddings = self.model.encode(text, convert_to_numpy=True)
            
            # 如果是单个文本，返回一维列表
            if isinstance(text, str):
                return embeddings.tolist()
            else:
                return embeddings.tolist()
                
        except Exception as e:
            print(f"向量化失败: {e}")
            raise
    
    def encode_single_text(self, text: str) -> List[float]:
        """编码单个文本"""
        return self.encode_text(text)
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示（encode_single_text的别名）"""
        return self.encode_single_text(text)
    
    def encode_batch_texts(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        return self.encode_text(texts)
    
    def compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def find_most_similar(self, query_vector: List[float], candidate_vectors: List[List[float]], top_k: int = 5) -> List[tuple]:
        """找到最相似的向量"""
        similarities = []
        
        for i, candidate in enumerate(candidate_vectors):
            similarity = self.compute_similarity(query_vector, candidate)
            similarities.append((i, similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        if not self.model:
            return {"status": "not_loaded"}
        
        return {
            "model_name": self.model_name,
            "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown'),
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "status": "loaded"
        } 