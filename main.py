# FastAPI 应用入口点
# 保持最小化，将业务逻辑委托给 src/reporter 包

from fastapi import FastAPI

app = FastAPI(
    title="Data Analysis Report Tool",
    description="Web-based automated data analysis and reporting tool for time-series data",
    version="0.1.0"
)

@app.get("/")
async def root():
    """主页面 - 临时响应，后续将提供 HTML 模板"""
    return {"message": "Data Analysis Report Tool"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)