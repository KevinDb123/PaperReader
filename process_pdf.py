# process_pdf.py

import fitz  # PyMuPDF
import os
import collections

# 这个函数保持不变
def extract_text_and_identify_titles(pdf_path):
    doc = fitz.open(pdf_path)
    document_data = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_info = { "text": span["text"].strip(), "size": round(span["size"]) }
                        if text_info["text"]:
                            document_data.append(text_info)
    doc.close()
    return document_data

# 这个函数保持不变
def segment_by_titles(document_data):
    if not document_data: return []
    font_sizes = [item['size'] for item in document_data]
    size_counts = collections.Counter(font_sizes)
    main_text_size = size_counts.most_common(1)[0][0]
    title_threshold = main_text_size + 1 # 稍微降低阈值以捕捉更多标题

    sections = []
    current_section = {"title": "Introduction", "content": ""}
    for item in document_data:
        if item['size'] > title_threshold and len(item['text'].split()) < 30:
            if current_section['content'].strip():
                sections.append(current_section)
            current_section = {"title": item['text'], "content": ""}
        else:
            current_section['content'] += item['text'] + " "
    if current_section['content'].strip():
        sections.append(current_section)
    return sections

# 这个函数保持不变
def save_sections_to_markdown(sections, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for section in sections:
            title = section['title']
            content = section['content'].strip()
            f.write(f"## {title}\n\n{content}\n\n")

# 【新增】这是供 main.py 调用的主函数
def run_pdf_processing(pdf_path: str, md_output_path: str):
    """
    执行从 PDF 到 Markdown 的完整流程。
    """
    print(f"--- Running PDF Processing for {pdf_path} ---")
    all_text_data = extract_text_and_identify_titles(pdf_path)
    paper_sections = segment_by_titles(all_text_data)
    if paper_sections:
        save_sections_to_markdown(paper_sections, md_output_path)
        print(f"Successfully created Markdown file at {md_output_path}")
        return True
    else:
        print("Warning: No sections could be extracted from the PDF.")
        return False