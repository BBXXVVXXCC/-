import os

def validate_docs():
    docs_folder = "docs"
    print(f"详细验证 {docs_folder} 文件夹...\n")
    
    if not os.path.exists(docs_folder):
        print("❌ docs 文件夹不存在！")
        return
    
    files = os.listdir(docs_folder)
    
    valid_files = []
    invalid_files = []
    
    for filename in files:
        filepath = os.path.join(docs_folder, filename)
        if os.path.isdir(filepath):
            continue
        
        size = os.path.getsize(filepath)
        
        if filename.startswith("._"):
            invalid_files.append({
                "filename": filename,
                "size": size,
                "reason": "macOS元数据文件"
            })
        elif filename.endswith(".zip"):
            invalid_files.append({
                "filename": filename,
                "size": size,
                "reason": "压缩包，不支持"
            })
        elif filename.endswith((".md", ".txt", ".pdf", ".docx")):
            # 检查是否是真正的文本内容
            try:
                if filename.endswith((".md", ".txt")):
                    with open(filepath, "rb") as f:
                        preview = f.read(200)
                    
                    is_text = True
                    try:
                        preview.decode("utf-8")
                    except:
                        is_text = False
                    
                    if is_text and len(preview.strip()) > 0:
                        valid_files.append({
                            "filename": filename,
                            "size": size,
                            "status": "✅ 有效"
                        })
                    else:
                        invalid_files.append({
                            "filename": filename,
                            "size": size,
                            "reason": "可能不是有效的文本内容"
                        })
                else:
                    valid_files.append({
                        "filename": filename,
                        "size": size,
                        "status": "✅ 支持格式"
                    })
            except Exception as e:
                invalid_files.append({
                    "filename": filename,
                    "size": size,
                    "reason": f"读取错误: {e}"
                })
        else:
            invalid_files.append({
                "filename": filename,
                "size": size,
                "reason": "不支持的格式"
            })
    
    print("="*80)
    print("【有效文档】")
    print("="*80)
    for f in valid_files:
        size_mb = f["size"] / 1024 / 1024
        print(f"{f['status']} {f['filename']} ({size_mb:.2f} MB)")
    
    print("\n" + "="*80)
    print("【无效文档】")
    print("="*80)
    for f in invalid_files:
        size_kb = f["size"] / 1024
        print(f"❌ {f['filename']} ({size_kb:.2f} KB) - {f['reason']}")
    
    print(f"\n总结：有效文档 {len(valid_files)} 个，无效文档 {len(invalid_files)} 个")
    
    return valid_files, invalid_files

if __name__ == "__main__":
    validate_docs()
