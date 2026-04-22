# Qwen 3.5:9B Multimodal API Service

A production-ready Docker-based API service for the Qwen 3.5:9B vision model running on Ollama. Provides image analysis capabilities with text prompts, featuring asynchronous request handling, concurrent request limiting, and comprehensive programmatic clients.

**Status**: ✅ Production Ready | 🔒 HTTPS Enabled | 📦 Docker Optimized | 🚀 RTX 4090 Optimized

---

## 🎯 Overview

This project provides a FastAPI-based wrapper around Qwen 3.5:9B running on Ollama, enabling:

- **Image Analysis**: Upload images + text prompts → AI-generated analysis
- **Multimodal Processing**: Vision + language understanding in a single request
- **Asynchronous API**: Non-blocking concurrent request handling
- **Rate Limiting**: Configurable concurrent request limits (default: 10)
- **Docker Deployment**: Complete containerization with docker-compose
- **HTTPS Support**: Self-signed certificate support for secure communication
- **Programmatic Clients**: Python libraries for sync, async, and batch operations

---

## 📋 Requirements

### Hardware
- **GPU**: RTX 4090 (or compatible NVIDIA GPU with 24GB+ VRAM)
- **RAM**: 32GB+ system RAM recommended
- **Storage**: 30GB+ for model weights

### Software
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Ollama**: Latest version running locally
- **Python**: 3.9+ (for CLI and client libraries)

---

## 🚀 Quick Start

### 1. Prerequisites Setup

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the Qwen model
ollama pull qwen3.5:9b
```

### 2. Project Setup

```bash
# Clone/setup project directory
cd qwen-api-service

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create .env file (auto-generated with defaults)
python3 docker-cli.py status

# Edit .env if needed (optional)
nano .env
```

**Default .env Configuration:**
```env
OLLAMA_BASE_URL=http://172.17.0.1:11434
MODEL_NAME=qwen3.5:9b
API_HOST=0.0.0.0
API_PORT=8000
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=300
LOG_LEVEL=INFO
```

### 4. Build & Run

```bash
# Complete build and run workflow
python3 docker-cli.py build-and-run

# Or step-by-step:
python3 docker-cli.py build              # Build image
python3 docker-cli.py run-compose        # Run with docker-compose
python3 docker-cli.py health             # Check health
python3 docker-cli.py test               # Test endpoint
```

---

## 🛠️ Docker CLI Management

The `docker-cli.py` script provides comprehensive Docker management with integrated .env configuration support.

### Common Commands

```bash
# Status & Information
python3 docker-cli.py status              # Show full status + config
python3 docker-cli.py check               # Check Docker and Ollama
python3 docker-cli.py health              # Health check (with retries)

# Build & Deploy
python3 docker-cli.py build               # Build image
python3 docker-cli.py build --no-cache    # Force rebuild
python3 docker-cli.py build-and-run       # Build + run (recommended)
python3 docker-cli.py run                 # Run with docker run (legacy)
python3 docker-cli.py run-compose         # Run with docker-compose

# Monitoring
python3 docker-cli.py logs                # Show last 100 lines
python3 docker-cli.py logs -f             # Follow logs (tail -f)
python3 docker-cli.py logs -n 500         # Show last 500 lines
python3 docker-cli.py test                # Test API endpoint

# Management
python3 docker-cli.py shell               # Open container shell
python3 docker-cli.py stop                # Stop container
python3 docker-cli.py full-reset          # Complete reset (removes all)
```

### Health Check Output

```
=== Health Check (max 30s) ===

✓ Service is healthy!

  Status: healthy
  Model: qwen3.5:9b
  Ollama URL: http://172.17.0.1:11434
  Max Concurrent: 10
  API Version: 1.1.0
  Log Level: INFO
```

---

## 📡 API Usage

### HTTP Endpoint

```bash
curl -k -X POST https://localhost:8443/generate-with-image \
  -F "image=@/path/to/image.png" \
  -F "prompt=What do you see in this image?" \
  -o response.json
```

**Request Parameters:**
- `image` (file, required): PNG, JPEG, GIF, or WebP image file
- `prompt` (text, required): Your question or analysis request

**Response:**
```json
{
  "response": "The image contains a detailed analysis...",
  "model": "qwen3.5:9b",
  "timestamp": "2024-04-11T10:30:45.123456",
  "metrics": {
    "total_duration": 12.34,
    "load_duration": 2.15,
    "prompt_eval_count": 156,
    "prompt_eval_duration": 1.23,
    "eval_count": 284,
    "eval_duration": 8.96
  }
}
```

### Health Check Endpoint

```bash
curl -s https://localhost:8443/health | jq .
```

---

## 🐍 Programmatic Clients

Three different client approaches for integrating into your Python applications:

### 1. Synchronous Client

**Best for**: Simple scripts, blocking workflows

```python
from clients.image_generation import generate_with_image

# Single image analysis
result = generate_with_image(
    image_path="./image.png",
    prompt="What is in this image?",
    output_file="response.md",  # Auto-saves as markdown
    as_markdown=True,
    timeout=300
)

print(result['response'])
print(f"Duration: {result['metrics']['total_duration']}s")
```

**Features:**
- Simple blocking API
- Automatic file handle management
- Output file auto-format detection (.md or .json)
- Built-in error handling

### 2. Asynchronous Client

**Best for**: High-performance applications, concurrent processing

```python
import asyncio
from clients.image_generation import generate_with_image_async

async def analyze_image():
    result = await generate_with_image_async(
        image_path="./image.png",
        prompt="Describe this image",
        output_file="response.md",
        timeout=300
    )
    
    print(result['response'])
    return result

# Run in async context
response = asyncio.run(analyze_image())
```

**Features:**
- Non-blocking async/await pattern
- Optimal for concurrent requests
- HTTPS support with self-signed certificates
- Progress logging with image names

### 3. Batch Processing Client

**Best for**: Processing multiple images with rate limiting

```python
import asyncio
from clients.image_generation import batch_generate_with_images

async def process_images():
    images = [
        {
            "path": "image1.png",
            "prompt": "What's the main subject?",
            "output_file": "output1.md"
        },
        {
            "path": "image2.png",
            "prompt": "Describe the composition",
            "output_file": "output2.md"
        },
        {
            "path": "image3.png",
            "prompt": "What colors are prominent?",
            "output_file": "output3.json",  # Different format
            "as_markdown": False
        }
    ]
    
    results = await batch_generate_with_images(
        images=images,
        max_concurrent=2,      # Limit to 2 concurrent requests
        timeout=300
    )
    
    print(f"✅ {len(results['successful'])} successful")
    print(f"❌ {len(results['failed'])} failed")
    
    return results

# Run batch processing
results = asyncio.run(process_images())
```

**Features:**
- Concurrent request limiting with asyncio.Semaphore
- Per-image format control (markdown vs JSON)
- Indexed progress logging `[1/3], [2/3], [3/3]`
- Automatic parent directory creation
- Failure isolation (one failure doesn't halt batch)

---

## 🧪 Test Suite

Comprehensive test suite demonstrating all client functions:

```bash
# Prepare test environment
mkdir -p images test_output
echo "Describe this image in detail" > default_prompt.txt
cp /path/to/test/image.png images/

# Run full test suite
python3 test_image_generation.py
```

**Test Coverage:**
1. **Synchronous Generation** - Single image per test
2. **Asynchronous Generation** - Single image per test
3. **Batch Generation** - Multiple images concurrently

**Test Output Structure:**
```
test_output/
├── sync/           # Synchronous results
│   ├── image1.json
│   └── image2.json
├── async/          # Asynchronous results
│   ├── image1.json
│   └── image2.json
├── batch/          # Batch processing results
│   ├── image1.json
│   └── image2.json
└── test_results.json  # Summary report
```

**Test Results Report:**
```json
{
  "summary": {
    "passed": 8,
    "failed": 0,
    "total": 8
  },
  "results": [
    {
      "test_name": "Test 1: Sync Generation (image1.png)",
      "status": "PASSED",
      "duration": 12.34,
      "details": {
        "result": "The image shows..."
      },
      "timestamp": "2024-04-11T10:30:45"
    }
  ]
}
```

---

## 📁 Project Structure

```
qwen-api-service/
├── app.py                          # FastAPI application
├── config.py                       # Configuration management
├── docker-cli.py                   # Docker management CLI
├── test_image_generation.py        # Comprehensive test suite
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Container orchestration
├── requirements.txt                # Python dependencies
├── .env                            # Environment config (auto-generated)
├── .env.example                    # Config template
├── clients/
│   ├── __init__.py
│   └── image_generation.py         # Client libraries
├── certs/                          # SSL certificates (HTTPS)
│   ├── cert.pem
│   └── key.pem
├── images/                         # Test images
├── test_output/                    # Test results
└── logs/                           # Application logs
```

---

## 🔧 Configuration

All settings are managed via `.env` file:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://172.17.0.1:11434` | Ollama service URL |
| `MODEL_NAME` | `qwen3.5:9b` | Vision model to use |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API listen port |
| `MAX_CONCURRENT_REQUESTS` | `10` | Concurrent request limit |
| `REQUEST_TIMEOUT` | `300` | Request timeout (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum image size |
| `ALLOWED_IMAGE_FORMATS` | `JPEG,PNG,GIF,WEBP` | Supported formats |

**Modify configuration:**
```bash
# Edit .env file
nano .env

# Rebuild and restart
python3 docker-cli.py build-and-run
```

---

## 🔒 HTTPS & Security

The API supports HTTPS with self-signed certificates:

```bash
# Generate self-signed certificates (if needed)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out certs/cert.pem -keyout certs/key.pem -days 365

# Access via HTTPS (with curl -k flag for self-signed)
curl -k https://localhost:8443/health
```

**Client Configuration:**
```python
# Automatically handles self-signed certificates
result = await generate_with_image_async(
    image_path="./image.png",
    prompt="Analyze this",
    api_url="https://localhost:8443",  # HTTPS endpoint
    timeout=300
)
```

---

## 📊 Performance Tuning

### Concurrent Requests

Adjust based on GPU VRAM:

```env
# For RTX 4090 (24GB) - recommended
MAX_CONCURRENT_REQUESTS=10

# For RTX 3090 (24GB)
MAX_CONCURRENT_REQUESTS=6

# For RTX 4070 (12GB)
MAX_CONCURRENT_REQUESTS=3
```

### Request Timeout

Increase for complex images/prompts:

```env
# Default: 300s (5 minutes)
REQUEST_TIMEOUT=600  # 10 minutes for large batches
```

### Batch Processing

Control concurrency in batch operations:

```python
results = await batch_generate_with_images(
    images=batch_images,
    max_concurrent=2,     # Limit to 2 at a time
    timeout=600
)
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check Docker is running
docker ps

# View detailed logs
python3 docker-cli.py logs -f

# Check Ollama connectivity
python3 docker-cli.py check
```

### Health Check Fails

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check model is loaded
ollama list | grep qwen3.5

# Pull if missing
ollama pull qwen3.5:9b
```

### Image Processing Fails

```bash
# Verify image format
file image.png  # Should show PNG

# Check file permissions
ls -la image.png

# Try with different image
python3 -c "from PIL import Image; Image.open('image.png')"
```

### Memory Issues

```bash
# Monitor GPU usage
nvidia-smi

# Reduce concurrent requests
# Edit .env: MAX_CONCURRENT_REQUESTS=2

# Increase timeout
# Edit .env: REQUEST_TIMEOUT=600
```

---

## 📝 Output File Formats

The client automatically detects output format from file extension:

```python
# Save as markdown
generate_with_image(
    image_path="test.png",
    prompt="Describe this",
    output_file="response.md"  # → response.md
)

# Save as JSON
generate_with_image(
    image_path="test.png",
    prompt="Describe this",
    output_file="response.json"  # → response.json
)

# Auto-detect based on flag
generate_with_image(
    image_path="test.png",
    prompt="Describe this",
    output_file="response",
    as_markdown=True  # → response.md
)
```

---

## 🚀 Production Deployment

### Docker Compose (Recommended)

```bash
# Start service
python3 docker-cli.py build-and-run

# Monitor
python3 docker-cli.py logs -f

# Scale (requires docker-compose adjustment)
# Edit docker-compose.yml and re-run
```

### Manual Docker Run

```bash
# Build
docker build -t qwen-api-service:latest .

# Run
docker run -d \
  --name qwen-api-service \
  --publish 8000:8000 \
  --env OLLAMA_BASE_URL=http://172.17.0.1:11434 \
  --env MODEL_NAME=qwen3.5:9b \
  --restart unless-stopped \
  qwen-api-service:latest
```

### Kubernetes (Future)

The Docker image can be deployed to Kubernetes with appropriate resource limits for GPU access.

---

## 📚 API Documentation

Once running, access interactive API docs:

```
🔗 Swagger UI:    http://localhost:8000/docs
🔗 ReDoc:         http://localhost:8000/redoc
🔗 OpenAPI JSON:  http://localhost:8000/openapi.json
```

---

## 🤝 Contributing

Issues and improvements welcome! The modular structure makes it easy to:
- Add new endpoints
- Implement different models
- Extend client libraries
- Improve documentation

---

## 📄 License

This project is provided as-is for research and production use.

---

## 🔗 Useful Links

- **Ollama**: https://ollama.ai
- **Qwen Model**: https://huggingface.co/Qwen/Qwen-VL-Chat
- **FastAPI**: https://fastapi.tiangolo.com
- **Docker**: https://www.docker.com

---

## 💡 Quick Reference

```bash
# Most common workflow
python3 docker-cli.py build-and-run    # Deploy
python3 docker-cli.py logs -f          # Monitor
python3 test_image_generation.py       # Test

# Integration examples
curl -k -X POST https://localhost:8443/generate-with-image \
  -F "image=@image.png" -F "prompt=What's in this?" 

python3 -c "
from clients.image_generation import generate_with_image
result = generate_with_image('image.png', 'Describe this')
print(result['response'])
"
```

---

**Status**: ✅ Ready for Production | 🚀 Optimized for RTX 4090 | 📦 Fully Containerized