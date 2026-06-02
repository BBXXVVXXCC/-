import os

def check_docs():
    docs_folder = "docs"
    print(f"检查 {docs_folder} 文件夹...\n")
    
    if not os.path.exists(docs_folder):
        print("❌ docs 文件夹不存在！")
        return
    
    files = os.listdir(docs_folder)
    print(f"发现 {len(files)} 个文件：\n")
    
    valid_files = []
    invalid_files = []
    
    for filename in files:
        filepath = os.path.join(docs_folder, filename)
        is_dir = os.path.isdir(filepath)
        size = os.path.getsize(filepath) if not is_dir else 0
        
        if filename.startswith("._"):
            print(f"🚫 {filename} (元数据文件，大小: {size} bytes)")
            invalid_files.append(filename)
        else:
            print(f"✅ {filename} (大小: {size} bytes)")
            valid_files.append(filename)
    
    print(f"\n总结：")
    print(f"  有效文档数：{len(valid_files)}")
    print(f"  无效元数据文件：{len(invalid_files)}")
    
    if len(valid_files) == 0:
        print("\n❌ 没有找到有效的文档文件！")
        print("请确保 docs 文件夹中有真正的 .md/.txt/.pdf/.docx 文件")
    else:
        print("\n✅ 找到了有效文档！")

if __name__ == "__main__":
    check_docs()
