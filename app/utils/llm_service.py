import aiohttp
import json
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings

class LLMService:
    """大语言模型服务"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_url = settings.deepseek_api_url
        self.model = settings.deepseek_model
        
    async def generate_answer(self, query: str, context: List[str], max_tokens: int = 1000) -> str:
        """生成答案"""
        if not self.api_key:
            return self._generate_fallback_answer(query, context)
        
        try:
            # 构建上下文
            context_text = "\n\n".join(context)
            
            # 构建提示词
            prompt = self._build_prompt(query, context_text)
            print("📝 喂给LLM的prompt如下：")
            print(prompt)
            
            # 调用API
            response = await self._call_api(prompt, max_tokens)
            return response
            
        except Exception as e:
            print(f"调用DeepSeek API失败: {e}")
            return self._generate_fallback_answer(query, context)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """构建提示词"""
        prompt = f"""基于以下上下文信息，回答用户的问题。如果上下文中没有相关信息，请说明无法从提供的信息中找到答案。

上下文信息：
{context}

用户问题：{query}

请提供准确、简洁的回答："""
        return prompt
    
    async def _call_api(self, prompt: str, max_tokens: int) -> str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API调用失败: {response.status} - {error_text}")
    
    def _generate_fallback_answer(self, query: str, context: List[str]) -> str:
        """生成备选答案（当API不可用时）"""
        if not context:
            return "抱歉，没有找到相关的上下文信息来回答您的问题。"
        
        # 简单的关键词匹配
        query_lower = query.lower()
        relevant_contexts = []
        
        for ctx in context:
            ctx_lower = ctx.lower()
            # 简单的关键词匹配
            if any(word in ctx_lower for word in query_lower.split()):
                relevant_contexts.append(ctx)
        
        if relevant_contexts:
            # 返回最相关的上下文片段
            return f"根据相关信息：\n{relevant_contexts[0][:200]}..."
        else:
            return f"根据提供的上下文信息，我找到了以下相关内容：\n{context[0][:200]}..."
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self.api_key:
            return {
                "status": "warning",
                "message": "DeepSeek API密钥未配置，将使用备选模式",
                "api_available": False
            }
        
        try:
            # 简单的API测试
            test_prompt = "你好"
            await self._call_api(test_prompt, 10)
            return {
                "status": "healthy",
                "message": "DeepSeek API连接正常",
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"DeepSeek API连接失败: {str(e)}",
                "api_available": False
            } 