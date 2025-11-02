# split_markdown.py

import os
import re

# 这个函数保持不变
def sanitize_filename(title):
    s = title.strip().replace(' ', '_').replace('.', '_')
    s = re.sub(r'[^\w_]', '', s)
    s = s.lower()
    s = re.sub(r'__+', '_', s)
    # 避免空文件名，并限制长度
    return f"{s[:50]}.txt" if s else "section.txt"

# 【改造】这个函数现在会返回一个文件路径列表
def parse_and_split_markdown(md_path, output_dir):
    """
    解析Markdown文件，切分为多个txt，并返回所有创建文件的路径列表。
    """
    print(f"--- Splitting Markdown {md_path} into sections ---")
    os.makedirs(output_dir, exist_ok=True)
    
    # 清空旧文件
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))

    saved_files = [] # 用于存储创建的文件路径
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input markdown file '{md_path}' not found.")
        return [] # 返回空列表

    # ... (您原来的所有切分逻辑保持不变)
    abstract_start_index = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == '## abstract':
            abstract_start_index = i
            break
            
    if abstract_start_index == -1:
        header_lines, abstract_lines, lines_after_abstract = [], [], lines
    else:
        header_lines = lines[:abstract_start_index]
        abstract_end_index = len(lines)
        for i in range(abstract_start_index + 1, len(lines)):
            if lines[i].strip().startswith('## '):
                abstract_end_index = i
                break
        abstract_lines = lines[abstract_start_index + 1 : abstract_end_index]
        lines_after_abstract = lines[abstract_end_index:]

    if header_lines:
        filepath = os.path.join(output_dir, "header_info.txt")
        with open(filepath, 'w', encoding='utf-8') as f: f.writelines(header_lines)
        saved_files.append(filepath)
    if abstract_lines:
        filepath = os.path.join(output_dir, "abstract.txt")
        with open(filepath, 'w', encoding='utf-8') as f: f.writelines(abstract_lines)
        saved_files.append(filepath)

    references_start_index = -1
    for i, line in enumerate(lines_after_abstract):
        if line.strip().lower() in ['## references', '## bibliography']:
            references_start_index = i
            break

    main_body_lines = lines_after_abstract[:references_start_index] if references_start_index != -1 else lines_after_abstract
    
    current_section_lines = []
    current_title = "introduction" # 给第一部分一个默认标题

    for line in main_body_lines:
        match = re.match(r'^##\s(.*)', line.strip())
        if match:
            if current_title and current_section_lines:
                filename = sanitize_filename(current_title)
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f: f.writelines(current_section_lines)
                saved_files.append(filepath)
            current_title = match.group(1).strip()
            current_section_lines = [line]
        else:
            current_section_lines.append(line)
            
    if current_title and current_section_lines:
        filename = sanitize_filename(current_title)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f: f.writelines(current_section_lines)
        saved_files.append(filepath)

    print(f"Successfully split into {len(saved_files)} section files.")
    return saved_files # 【重要】返回文件列表