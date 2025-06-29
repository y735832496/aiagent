import re
import tiktoken
from typing import List, Dict, Any
from app.config import settings

class TextProcessor:
    """文本处理工具类"""
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除页眉页脚等无关内容
        text = re.sub(r'第\s*\d+\s*页', '', text)
        text = re.sub(r'Page\s*\d+', '', text)
        
        # 移除广告相关内容
        ad_patterns = [
            r'广告',
            r'推广',
            r'点击',
            r'关注',
            r'订阅',
            r'分享',
            r'点赞'
        ]
        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()""''-]', '', text)
        
        return text.strip()
    
    def split_text(self, text: str) -> List[str]:
        """将文本分割成块"""
        # 首先清洗文本
        text = self.clean_text(text)
        
        # 使用tiktoken计算token数量
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = start + self.chunk_size
            
            # 如果还有更多token，尝试在句子边界分割
            if end < len(tokens):
                # 寻找最近的句子结束位置
                sentence_end = self._find_sentence_boundary(tokens, start, end)
                if sentence_end > start:
                    end = sentence_end
            
            # 解码token块
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
            
            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _find_sentence_boundary(self, tokens: List[int], start: int, end: int) -> int:
        """在token范围内寻找句子边界"""
        # 常见的句子结束标记（包括中文标点）
        sentence_endings = ['.', '!', '?', '。', '！', '？', '\n', '；', ';', '：', ':']
        
        # 优先在段落边界分割
        for i in range(end - 1, start, -1):
            if i < len(tokens):
                token_text = self.encoding.decode([tokens[i]])
                if '\n' in token_text:
                    return i + 1
        
        # 然后在句子边界分割
        for i in range(end - 1, start, -1):
            if i < len(tokens):
                token_text = self.encoding.decode([tokens[i]])
                if any(ending in token_text for ending in sentence_endings):
                    return i + 1
        
        # 最后在逗号等分隔符处分割
        comma_endings = [',', '，', '、']
        for i in range(end - 1, start, -1):
            if i < len(tokens):
                token_text = self.encoding.decode([tokens[i]])
                if any(ending in token_text for ending in comma_endings):
                    return i + 1
        
        return end
    
    def extract_metadata(self, text: str, filename: str = None) -> Dict[str, Any]:
        """提取文本元数据"""
        metadata = {
            'length': len(text),
            'word_count': len(text.split()),
            'chunk_count': len(self.split_text(text)),
            'filename': filename,
            'language': self._detect_language(text)
        }
        
        # 提取可能的标题
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100 and not first_line.endswith('.'):
                metadata['title'] = first_line
        
        return metadata
    
    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 检测中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'\w', text))
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return 'zh'
        else:
            return 'en' 