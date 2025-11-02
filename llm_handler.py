# llm_handler.py

import os
from openai import OpenAI

# 内部函数，负责实际的API调用
def _call_llm(api_key: str, model: str, messages: list):
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if "maximum context length" in str(e):
             raise ValueError("处理的文本内容过长，已超出模型处理上限。请尝试上传一篇页数较少的论文。")
        raise ValueError(f"与LLM API交互时出错: {e}")

# 总结函数，适配了新的 _call_llm 调用方式
def generate_summary(section_paths: list[str], api_key: str, model: str) -> str:
    print("--- Generating summary from section files ---")
    full_text_list = []
    for path in section_paths:
        with open(path, 'r', encoding='utf-8') as f:
            full_text_list.append(f.read())
    
    combined_text = "\n\n---\n\n".join(full_text_list)

    system_prompt = "你是一位AI领域的专业的科研分析师。你将收到一篇经过初步处理的论文内容。你的任务是基于这些信息，以一种全面、深入且结构化的方式，对这篇论文进行彻底的分析和解读。"
    user_prompt = f"""
    请根据以下提供的论文内容，为我生成一份详细的论文分析报告。报告必须严格按照以下结构组织，并对每个部分进行详尽的回答：
    1.  **基本信息**:论文标题是什么？作者是谁？
    2.  **论文结构**:简要描述这篇论文的整体组织结构（例如：引言、相关工作、方法、实验、结论）。
    3.  **前人研究综述 (Literature Review)**:请找出并总结论文中专门回顾和评述“前人研究”的章节（通常标题为 "Related Work"）。一一列出该章节中提到的主要研究方向、关键模型或代表性工作，并简要解释。
    4.  **核心问题 (Problem Statement)**:这篇论文具体致力于解决什么核心科学问题或技术挑战？
    5.  **关键方法 (Methodology)**:作者提出了什么独特的解决方案、关键方法、模型架构或算法来解决上述问题？
    6.  **重要公式 (Key Formulas)**:对比较重要的公式进行解释，说明其基本原理和在文中的作用。(如果没有明确的公式，请说明“文章中未提供具体的数学公式”)
    7.  **主要发现 (Key Findings & Results)**:作者通过实验得出了哪些最重要的结论或结果？
    8.  **价值与意义 (Value & Contribution)**:这项研究的主要贡献和学术价值是什么？与其他相关工作相比有哪些优势？
    9.  **批判性分析与展望 (Critical Analysis & Outlook)**:
    *   现在，请你扮演一位该领域的资深审稿人。
    *   **超越论文自身的论述**，并结合你庞大的知识库，请从以下几个方面对这项工作进行批判性评价：
        *   **创新性 (Innovation)**: 这项工作的核心思想有多新颖？
        *   **潜在影响 (Potential Impact)**: 它可能会对学术界或工业界产生哪些长远影响？
        *   **技术局限性 (Technical Limitations)**: 该方法或实验中，可能存在哪些潜在的弱点或局限性？
        *   **未来展望 (Future Work)**: 基于此，未来有哪些值得探索的研究方向？
    【论文内容】:
    {combined_text}
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return _call_llm(api_key, model, messages)

# 内部函数，专门用于压缩对话历史
def _summarize_history(chat_history: list, api_key: str, model: str) -> str:
    print("--- Compressing conversation history to save tokens ---")
    
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    
    system_prompt = "你是一个对话摘要机器人。你的任务是将一段多轮对话压缩成一段简短的摘要，保留所有关键信息、问题和结论。摘要将用于为下一轮对话提供上下文记忆。"
    user_prompt = f"请将以下对话历史压缩成一段摘要:\n\n---\n{history_str}\n---"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    summary = _call_llm(api_key, model, messages)
    print(f"  - Compressed history: {summary}")
    return summary

# 新的问答函数，集成了历史压缩逻辑
def answer_with_history(chat_history: list, question: str, section_paths: list[str], api_key: str, model: str) -> (str, list):
    """
    根据用户问题、对话历史和论文内容，生成回答。
    如果历史过长，会先进行压缩。
    返回: (回答文本, 更新后的历史记录)
    """
    print(f"--- Answering question with intelligent history management: '{question}' ---")
    
    HISTORY_COMPRESSION_THRESHOLD = 6 # 对话超过6轮 (3次问答) 就压缩
    if len(chat_history) > HISTORY_COMPRESSION_THRESHOLD:
        summary = _summarize_history(chat_history, api_key, model)
        updated_history = [{"role": "system", "content": f"先前对话的摘要: {summary}"}]
    else:
        updated_history = chat_history

    system_prompt = "你是一个严谨的论文问答机器人。你必须严格依据下面提供的【论文上下文】和我们的【对话历史摘要】来回答最新的【用户问题】。如果上下文没有提到相关内容，就自己思考，并在回答内容前面加上“根据提供的论文内容，我没有找到相关问题的答案，根据我自己的理解，”"

    if not updated_history:
        full_text_list = []
        for path in section_paths:
            with open(path, 'r', encoding='utf-8') as f:
                full_text_list.append(f.read())
        context = "\n\n---\n\n".join(full_text_list)
        
        user_prompt = f"【论文上下文】:\n{context}\n\n---\n【用户问题】:\n{question}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    else:
        messages = [{"role": "system", "content": system_prompt}] + updated_history + [{"role": "user", "content": question}]

    answer = _call_llm(api_key, model, messages)
    
    final_history = updated_history + [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    
    return answer, final_history