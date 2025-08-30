import ollama
r = ollama.chat(model="llama3.1:8b-instruct-q4_K_M",
                messages=[{"role":"user","content":"Summarize this article..."}])
print(r["message"]["content"])