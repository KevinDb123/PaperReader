# main.py

import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入您自己的模块！
import process_pdf
import split_markdown
# 【重要】确保导入了新的 answer_with_history 函数
import llm_handler

# --- App 初始化和配置 ---
app = FastAPI(title="智慧论文伴侣后端 (上下文压缩版)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义文件夹路径
UPLOAD_DIR = "uploads"
MD_DIR = "output_md"
SECTIONS_DIR = "output_sections"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)
os.makedirs(SECTIONS_DIR, exist_ok=True)

# 【重要】服务器状态现在包含 chat_history
paper_context = {
    "session_id": None, 
    "section_paths": [],
    "chat_history": []
}

class QuestionRequest(BaseModel):
    question: str

# --- API 接口定义 ---
@app.post("/summarize")
async def summarize_pdf(
    pdf_file: UploadFile = File(...),
    x_api_key: str = Header(...),
    x_model_name: str = Header(...)
):
    session_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{session_id}.pdf")
    md_path = os.path.join(MD_DIR, f"{session_id}.md")
    session_sections_dir = os.path.join(SECTIONS_DIR, session_id)
    
    try:
        # 1. 保存上传的PDF
        with open(pdf_path, "wb") as buffer:
            buffer.write(await pdf_file.read())
        
        # 2. 调用 process_pdf.py 的逻辑
        success = process_pdf.run_pdf_processing(pdf_path, md_path)
        if not success:
            raise HTTPException(status_code=500, detail="PDF处理失败，未能生成Markdown文件。")

        # 3. 调用 split_markdown.py 的逻辑
        section_paths = split_markdown.parse_and_split_markdown(md_path, session_sections_dir)
        if not section_paths:
            raise HTTPException(status_code=500, detail="Markdown切分失败，未能生成章节文件。")

        # 4. 【重要】更新并重置整个上下文
        paper_context["session_id"] = session_id
        paper_context["section_paths"] = section_paths
        paper_context["chat_history"] = [] # 为新论文清空聊天历史
        
        # 5. 调用 llm_handler.py 的逻辑
        summary = llm_handler.generate_summary(section_paths, x_api_key, x_model_name)
        
        return {"summary": summary}
    
    except ValueError as e: # 捕获来自 llm_handler 的 API 错误
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
    finally:
        # 6. 清理临时文件
        if os.path.exists(pdf_path): os.remove(pdf_path)
        if os.path.exists(md_path): os.remove(md_path)

@app.post("/ask")
async def ask_question_endpoint(
    request: QuestionRequest,
    x_api_key: str = Header(...),
    x_model_name: str = Header(...)
):
    if not paper_context["section_paths"]:
        raise HTTPException(status_code=400, detail="请先上传并总结一篇论文。")

    try:
        # 【重要】调用新的、返回两个值的函数
        answer, updated_history = llm_handler.answer_with_history(
            chat_history=paper_context["chat_history"],
            question=request.question,
            section_paths=paper_context["section_paths"],
            api_key=x_api_key,
            model=x_model_name
        )
        
        # 【重要】用返回的新历史覆盖旧历史
        paper_context["chat_history"] = updated_history

        return {"answer": answer}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")