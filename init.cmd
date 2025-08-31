@echo off
setlocal enabledelayedexpansion

set OLLAMA_URL=http://localhost:11434
set QDRANT_URL=http://localhost:6333
set /a MAX_RETRIES=30
set /a SLEEP_SEC=2

docker compose up -d
if errorlevel 1 (
  echo [ERROR] docker compose up failed.
  exit /b 1
)

echo Ollama ready check (%OLLAMA_URL%) ===
set /a i=0
:wait_ollama
curl -fsS %OLLAMA_URL%/api/tags >nul 2>&1
if errorlevel 1 (
  if !i! GEQ %MAX_RETRIES% (
    echo [ERROR] Ollama not responding after %MAX_RETRIES% tries.
    goto :fail
  )
  set /a i+=1
  timeout /t %SLEEP_SEC% /nobreak >nul
  goto :wait_ollama
)
echo Ollama is up.

:models
echo Pull Ollama models
curl -s %OLLAMA_URL%/api/pull -H "Content-Type: application/json" -d "{\"name\":\"nomic-embed-text\"}" | more
if errorlevel 1 echo [WARN] Failed to pull nomic-embed-text (will continue).
curl -s %OLLAMA_URL%/api/pull -H "Content-Type: application/json" -d "{\"name\":\"llama3.1:8b-instruct-q4_K_M\"}" | more
if errorlevel 1 (
  echo [WARN] Tag llama3.1:8b-instruct-q4_K_M not found

)

pip install -r requirements.txt

echo Smoke test: embedding
curl -s %OLLAMA_URL%/api/embeddings -H "Content-Type: application/json" -d "{\"model\":\"nomic-embed-text\",\"prompt\":\"hello world\"}" >nul
if errorlevel 1 (
  echo [WARN] Embedding smoke test failed.
) else (
  echo Embedding endpoint OK.
)