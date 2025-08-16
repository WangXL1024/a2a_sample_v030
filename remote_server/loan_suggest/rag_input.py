from langchain_community.document_loaders import TextLoader
import redis
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv
import os

# add knowledge to RAG
def rag_ingest(file_path="loan_scheme_V2.txt"):
    #1、加载原始文档    
    loader = TextLoader(file_path,encoding='utf-8')
    documents = loader.load()
    #2、切分文档
    import re
    from langchain_text_splitters import CharacterTextSplitter
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0, separator="\n\n", keep_separator=True)
    texts = re.split(r"\n\n", documents[0].page_content)
    segments = text_splitter.split_text(documents[0].page_content)
    segment_documents = text_splitter.create_documents(texts)
    #3、将文档向量化，保存到Redis中
    embedding_model = DashScopeEmbeddings(model="text-embedding-v1",dashscope_api_key="xxx")
    redis_url = "redis://localhost:6379"
    config = RedisConfig(
        index_name="loan_scheme",
        redis_url=redis_url
    )
    vector_store = RedisVectorStore(embedding_model, config=config)
    vector_store.add_documents(segment_documents)
    return f"{len(segment_documents)} documents ingested to RAG Redis."


if __name__ == "__main__":
    # add base knowledge to RAG
    print(rag_ingest())
    # add additional knowledge to RAG
    # print(rag_ingest())