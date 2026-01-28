from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from datetime import datetime
import os, json, shutil

app = FastAPI()
os.makedirs("storage", exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Cloud Storage</title>
    <style>
        body {font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;}
        h1 {color: #333;}
        .endpoint {background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px;}
        .btn {display: inline-block; padding: 10px 20px; background: #007bff; color: white; 
              text-decoration: none; border-radius: 5px; margin: 5px;}
    </style>
    </head>
    <body>
        <h1>Облачное хранилище</h1>
        <p>Простое приложение для работы с файлами в Codespaces</p>
        
        <h2>Доступные функции:</h2>
        <div class="endpoint"><strong>POST /upload</strong> - Загрузить файл</div>
        <div class="endpoint"><strong>GET /list</strong> - Список файлов (JSON)</div>
        <div class="endpoint"><strong>GET /files/имя_файла</strong> - Скачать файл</div>
        
        <h2> Быстрый доступ:</h2>
        <a class="btn" href="/upload-form">Форма загрузки</a>
        <a class="btn" href="/list"> Список файлов</a>
        
        <h2> Информация:</h2>
        <p>Файлы сохраняются в папку <code>storage/</code> с разделением по датам</p>
        <p>Для каждого файла сохраняются метаданные (размер, дата загрузки)</p>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
 
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = f"storage/{today}"
    os.makedirs(date_folder, exist_ok=True)
    
  
    file_path = f"{date_folder}/{file.filename}"
    
    
    counter = 1
    original_name = file.filename
    while os.path.exists(file_path):
        name, ext = os.path.splitext(original_name)
        file_path = f"{date_folder}/{name}_{counter}{ext}"
        counter += 1
    
   
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
   
    metadata = {
        "original_name": original_name,
        "size": len(content),
        "upload_date": datetime.now().isoformat(),
        "content_type": file.content_type,
        "path": file_path.replace("storage/", "")
    }
    
    with open(f"{file_path}.meta.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    return {
        "status": "success",
        "message": "Файл загружен",
        "filename": os.path.basename(file_path),
        "size": len(content),
        "date_folder": today,
        "download_url": f"/files/{today}/{os.path.basename(file_path)}"
    }


@app.get("/list")
def list_files():
    all_files = []
    
    for root, dirs, files in os.walk("storage"):
        for file in files:
            if not file.endswith(".meta.json"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, "storage")
                
           
                file_info = {
                    "name": file,
                    "path": rel_path,
                    "url": f"/files/{rel_path}",
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
                
            
                meta_path = f"{file_path}.meta.json"
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            metadata = json.load(f)
                            file_info["metadata"] = metadata
                    except:
                        file_info["metadata"] = "error"
                
                all_files.append(file_info)
    
    return JSONResponse({
        "count": len(all_files),
        "files": all_files,
        "storage_info": {
            "total_size": sum(f["size"] for f in all_files),
            "folders": [d for d in os.listdir("storage") if os.path.isdir(f"storage/{d}")]
        }
    })


@app.get("/files/{date}/{filename}")
@app.get("/files/{filename}")
def download_file(date: str = None, filename: str = None):
    if date:
        file_path = f"storage/{date}/{filename}"
    else:

        for root, dirs, files in os.walk("storage"):
            if filename in files:
                file_path = os.path.join(root, filename)
                break
        else:
            file_path = f"storage/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(file_path, filename=filename)


@app.get("/upload-form", response_class=HTMLResponse)
def upload_form():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Загрузка файла</title>
    <style>
        body {font-family: Arial; margin: 40px;}
        form {max-width: 500px; margin: 0 auto;}
        input[type="file"] {padding: 10px; margin: 10px 0; border: 2px dashed #ccc; width: 100%;}
        input[type="submit"] {padding: 12px 24px; background: #28a745; color: white; 
                             border: none; border-radius: 5px; cursor: pointer; font-size: 16px;}
        .back {display: block; margin-top: 20px; color: #666;}
    </style>
    </head>
    <body>
        <h1> Загрузите файл</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br><br>
            <input type="submit" value="Загрузить">
        </form>
        <a href="/" class="back">← На главную</a>
        <a href="/list" class="back"> Посмотреть список файлов</a>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    print(" Все функции готовы:")
    print("  1. GET /           - Главная страница")
    print("  2. POST /upload    - Загрузка файлов")
    print("  3. GET /list       - JSON список")
    print("  4. GET /files/*    - Скачивание")
    print("  5. GET /upload-form - HTML форма")
    uvicorn.run(app, host="0.0.0.0", port=8010)