from typing import Dict, Optional
from src.config.load_key import load_key
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.embeddings import DashScopeEmbeddings
from pydantic import BaseModel, Field
from typing import List

# 定义返回结果的数据模型
class LoanSchemeResult(BaseModel):
    model_id: str
    schemes: List[str] = Field(default_factory=list)
    count: int = 0
    error: Optional[str] = None

class LoanSuggestService:
    """Encapsulate the RAG query logic of the existing auto loan scheme"""
    
    @staticmethod
    async def get_loan_scheme(model_id: Optional[str]) -> Dict:
        """
        Obtain the corresponding loan plan document from the Redis vector database based on the automobile model ID
        
        Args:
            model_id: the automobile model ID
            
        Returns:
            A dictionary containing information on loan schemes, whose structure conforms to the Loan-Schemeresult model
        """
        # 初始化结果对象
        result = LoanSchemeResult(model_id=model_id or "")
        
        if not model_id:
            result.error = "model_id cannot be empty."
            return result.model_dump()
        
        try:
            # 初始化嵌入模型
            embedding_model = DashScopeEmbeddings(
                model="text-embedding-v1",
                dashscope_api_key=load_key("DASHSCOPE_API_KEY"),
            )
            
            # 配置Redis向量存储
            redis_url = "redis://localhost:6379"
            config = RedisConfig(
                index_name="loan_scheme",
                redis_url=redis_url
            )
            
            # 创建向量存储实例
            vector_store = RedisVectorStore(embedding_model, config=config)
            
            # 获取检索器并检索相关文档
            retriever = vector_store.as_retriever(
                search_kwargs={"k": 20}  # 最多返回3个最相关的结果
            )
            
            # 调用检索器（使用to_thread适配同步方法为异步）
            docs = await retriever.ainvoke(model_id)
            
            # 处理检索结果
            result.schemes = [doc.page_content for doc in docs]
            result.count = len(docs)
            
        except Exception as e:
            result.error = f"Failed to get the loan scheme: {str(e)}"
        
        return result.model_dump()