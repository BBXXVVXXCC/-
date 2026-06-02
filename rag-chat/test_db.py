import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def test_database():
    try:
        print("1. 初始化嵌入模型...")
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
        print("   ✅ 嵌入模型加载成功")
        
        print("2. 加载向量数据库...")
        vectorstore = Chroma(
            persist_directory="chroma_db",
            embedding_function=embeddings
        )
        print("   ✅ 向量数据库加载成功")
        
        print("3. 查询数据库统计...")
        collection = vectorstore._client.get_or_create_collection("langchain")
        count = collection.count()
        collections = [c.name for c in vectorstore._client.list_collections()]
        print(f"   ✅ 数据库统计: {count} 个文档片段, 集合: {collections}")
        
        print("4. 测试相似度搜索...")
        results = vectorstore.similarity_search("管理", k=3)
        print(f"   ✅ 搜索成功，找到 {len(results)} 条结果")
        for i, doc in enumerate(results):
            print(f"      [{i+1}] {doc.page_content[:50]}...")
        
        return True
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("数据库连接测试")
    print("="*60)
    success = test_database()
    print("="*60)
    if success:
        print("✅ 数据库测试全部通过！")
    else:
        print("❌ 数据库测试失败，请检查错误信息")