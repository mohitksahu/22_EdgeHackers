# Pluto - Docker Build Commands

This document contains the individual Docker build commands for frontend and backend services.

## Quick Start (Recommended)

### Build and Run with Docker Compose
```powershell
cd f:\Pluto
docker-compose up -d --build
```

## Backend Build

### Build Backend Image
```powershell
cd f:\Pluto\backend
docker build -t pluto-backend:latest .
```

### Run Backend Container
```powershell
docker run -d `
  --name pluto-backend `
  -p 8000:8000 `
  -v f:\Pluto\data:/app/data `
  -v f:\Pluto\config:/app/config `
  pluto-backend:latest
```

### Backend Build with Tag
```powershell
docker build -t pluto-backend:v1.0.0 -t pluto-backend:latest .
```

## Frontend Build

### Build Frontend Image
```powershell
cd f:\Pluto\frontend
docker build -t pluto-frontend:latest .
```

### Run Frontend Container
```powershell
docker run -d `
  --name pluto-frontend `
  -p 80:80 `
  pluto-frontend:latest
```

### Frontend Build with Tag
```powershell
docker build -t pluto-frontend:v1.0.0 -t pluto-frontend:latest .
```

## Build Both (From Root Directory)

### Build Backend from Root
```powershell
cd f:\Pluto
docker build -t pluto-backend:latest -f backend/Dockerfile backend/
```

### Build Frontend from Root
```powershell
cd f:\Pluto
docker build -t pluto-frontend:latest -f frontend/Dockerfile frontend/
```

## Using Docker Compose (Optional)

### Build All Services
```powershell
cd f:\Pluto
docker-compose build
```

### Build Specific Service
```powershell
docker-compose build backend
docker-compose build frontend
```

### Build and Run
```powershell
docker-compose up -d --build
```

### Stop All Services
```powershell
docker-compose down
```

## Cleanup Commands

### Remove Containers
```powershell
docker rm -f pluto-backend pluto-frontend
```

### Remove Images
```powershell
docker rmi pluto-backend:latest pluto-frontend:latest
```

### Prune Unused Images
```powershell
docker image prune -f
```

## Check Status

### List Running Containers
```powershell
docker ps
```

### View Logs
```powershell
docker logs pluto-backend
docker logs pluto-frontend
```

### Follow Logs
```powershell
docker logs -f pluto-backend
docker logs -f pluto-frontend
```

cd f:\Pluto
>> 
>> # Stop and remove existing containers
>> docker rm -f pluto-backend pluto-frontend pluto-qdrant
>> 
>> # Run Qdrant (vector database)
>> docker run -d `
>>   --name pluto-qdrant `
>>   --network pluto-network `
>>   -p 6333:6333 `
>>   -p 6334:6334 `
>>   -v f:\Pluto\data\qdrant_storage:/qdrant/storage `
>>   qdrant/qdrant:latest
>> 
>> # Build and run Backend
>> cd f:\Pluto\backend
>> docker build -t pluto-backend:latest .
>> docker run -d `
>>   --name pluto-backend `
>>   --network pluto-network `
>>   -p 8000:8000 `
>>   -e QDRANT_HOST=pluto-qdrant `
>>   -e QDRANT_PORT=6333 `
>>   -v f:\Pluto\data:/app/data `
>>   -v f:\Pluto\config:/app/config `
>>   pluto-backend:latest
>>
>> # Build and run Frontend
>> cd f:\Pluto\frontend
>> docker build -t pluto-frontend:latest .
>> docker run -d `
>>   --name pluto-frontend `
>>   --network pluto-network `
>>   -p 80:80 `
>>   pluto-frontend:latest
>>
PS F:\Pluto> # Initialize the vector store collection
>> docker exec -it pluto-backend python -c "from app.storage.qdrant.client import QdrantClientWrapper; client = QdrantClientWrapper(); client.create_collection(); print('Collection created successfully!')"
Collection created successfully!
PS F:\Pluto> cd f:\Pluto
>>                                                                             
>> # Stop and remove existing containers                                       
>> docker rm -f pluto-backend pluto-frontend pluto-qdrant
>> 
>> # Run Qdrant (vector database)
>> docker run -d `
>>   --name pluto-qdrant `
>>   --network pluto-network `
>>   -p 6333:6333 `
>>   -p 6334:6334 `
>>   -v f:\Pluto\data\qdrant_storage:/qdrant/storage `
>>   qdrant/qdrant:latest
>> 
>> # Build and run Backend
>> cd f:\Pluto\backend
>> docker build -t pluto-backend:latest .
>> docker run -d `
>>   --name pluto-backend `
>>   --network pluto-network `
>>   -p 8000:8000 `
>>   -e QDRANT_HOST=pluto-qdrant `
>>   -e QDRANT_PORT=6333 `
>>   -v f:\Pluto\data:/app/data `
>>   -v f:\Pluto\config:/app/config `
>>   pluto-backend:latest
>>
>> # Build and run Frontend
>> cd f:\Pluto\frontend
>> docker build -t pluto-frontend:latest .
>> docker run -d `
>>   --name pluto-frontend `
>>   --network pluto-network `
>>   -p 80:80 `
>>   pluto-frontend:latest
>>


# Initialize the vector store collection
>> docker exec -it pluto-backend python -c "from app.storage.qdrant.client import QdrantClientWrapper; client = QdrantClientWrapper(); client.create_collection(); print('Collection created successfully!')"
Collection created successfully!


# Terminal 1: Make sure Ollama is running
ollama serve

# Terminal 2: Pull the model
ollama pull llama3.2:1b

# Terminal 3: Initialize system
cd F:\Pluto\backend
python scripts/init_system.py

# Terminal 3: Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000