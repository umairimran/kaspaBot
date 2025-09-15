## KaspaBot - Windows Setup Guide

### 1) Clone the repository
```powershell
git clone https://github.com/umairimran/kaspaBot
open the project
```

### 2) Create and activate a virtual environment
```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
```

### 3) Install requirements
```powershell
pip install -r requirements.txt
```

### 4) Create Qdrant storage folder
```powershell
mkdir qdrant_storage
```

### 5) Run Qdrant with Docker (use your project path)
```powershell
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v "C:\Users\User\Documents\kaspaBot\qdrant_storage:/qdrant/storage" qdrant/qdrant:latest
```

Make sure the `-v` path points to your project's `qdrant_storage` folder.

### 6) Migrate embeddings to Qdrant
```powershell
cd backend\db
python qdrant_utils.py migrate
```

You should see:
```
🎉 Successfully migrated 741 embeddings to Qdrant!
```

### 7) Create `.env` inside `backend/`
Create a file `backend/.env` for your environment variables (add your keys/configs as needed).

### 8) Run the backend
```powershell
cd ..
python main.py
```

### 9) Test with PowerShell
In a new PowerShell window:
```powershell
Invoke-RestMethod -Method Post -Uri "http://0.0.0.0:8001/ask" -ContentType "application/json" -Body '{"question":"What is Kaspa?","conversation_id":"temp1234","user_id":"local_test"}'
```

If everything is working, the API will return an answer.

### 10) Docker quick-start (build + run)
```powershell
docker compose up --build -d
```

### 11) Migrate FAISS embeddings into Qdrant (run once)
```powershell
docker compose exec -w /app/backend/db backend python qdrant_utils.py migrate
```