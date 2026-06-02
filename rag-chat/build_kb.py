# build_kb.py
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCS_FOLDER = "docs"
CHROMA_DB_FOLDER = "chroma_db"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

def main():
    print("1. 初始化嵌入模型...")
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
    print("   ✅ 嵌入模型加载成功")

    print("2. 删除旧的向量库...")
    import shutil
    if os.path.exists(CHROMA_DB_FOLDER):
        shutil.rmtree(CHROMA_DB_FOLDER)

    print("3. 加载测试文档...")
    documents = []
    test_file = os.path.join(DOCS_FOLDER, "test_document.md")
    
    if os.path.exists(test_file):
        try:
            loader = TextLoader(test_file, encoding="utf-8")
            docs = loader.load()
            documents.extend(docs)
            print(f"   ✅ 加载成功: test_document.md")
        except Exception as e:
            print(f"   ❌ 加载失败 test_document.md: {e}")
            return
    else:
        print("   ❌ 测试文档不存在")
        return
    
    print(f"   共加载 {len(documents)} 个文档")

    print("4. 切分文档...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            ".",
            "；",
            "，",
            " ",
            ""
        ],
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✅ 切分成 {len(chunks)} 个片段")
    for i, chunk in enumerate(chunks):
        print(f"      片段 {i+1}: 长度 {len(chunk.page_content)} 字符")
        preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"              {preview}...")

    print("5. 向量化并存入 Chroma...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_DB_FOLDER
    )
    print(f"✅ 向量库已保存到 {CHROMA_DB_FOLDER}")
    print(f"   包含 {len(chunks)} 个文档片段")

if __name__ == "__main__":
    main()