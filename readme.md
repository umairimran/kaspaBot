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
Install Docker :

sudo apt update && sudo apt install -y docker.io


Start docker:


sudo systemctl start docker
sudo systemctl enable docker


Check Version:
sudo docker --version

_______________________________________________________
Install docker compose :

🔧 Step 1: Add Docker’s official GPG key
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

_____________________________________________________
🔧 Step 2: Add Docker repository to apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null





🔧 Step 3: Update your package index (now includes Docker repo)
sudo apt update

✅ Step 4: Install Docker Compose Plugin
sudo apt install -y docker-compose-plugin

✅ Step 5: Verify Installation
docker compose version


_________________________________________________________-


_________________________________________________________-


Making of env:

cd backend
create .env place the credentials of all in this file

cd frontend
create .env place the 
VITE_API_URL=http://(Server Public IP):8000

Command for public ip:

curl http://checkip.amazonaws.com/

_________________________________________________________-






### 10) Docker quick-start (build + run)
```powershell
docker compose up --build -d
```

### 11) Migrate FAISS embeddings into Qdrant (run once)
```powershell
docker compose exec -w /app/backend/db backend python qdrant_utils.py migrate
```