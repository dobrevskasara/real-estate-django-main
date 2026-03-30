### 🐳 AI Model Setup

This project uses the `llama3:8b` AI model for automatic description generation.

### 🚀 Run Ollama with Docker

A `docker-compose.yml` file is provided for running Ollama.

Start the container and pull the AI model:

```bash
docker compose up -d
```
```bash
docker exec -it ollama ollama pull llama3:8b
```
```bash
docker exec -it ollama ollama list
```