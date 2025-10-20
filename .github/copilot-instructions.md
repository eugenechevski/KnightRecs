# KnightRecs - AI Coding Agent Instructions

## Project Overview
KnightRecs is a containerized movie recommendation system using SVD (Singular Value Decomposition) Collaborative Filtering. The system is designed for AWS ECS/Fargate deployment with a REST API interface. Built for KnightHacks 8 hackathon (Oct 24-26).

**Dataset**: MovieLens `ml-latest` (33.8M ratings, 86K movies, 331K users, Jan 1995 - Jul 2023) located in `ml-latest/`

## Architecture & Data Flow

```
User Request → Flask API (port 5000) → Trained SVD Model → Top-N Recommendations
                    ↓                           ↑
              Docker Container              model.pkl
                    ↓                    (scikit-surprise)
              AWS ECR Image
                    ↓
            ECS Fargate Service (0.5 vCPU, 1GB RAM)
```

**Core files**: `ratings.csv` (userId, movieId, rating, timestamp) + `movies.csv` (movieId, title, genres)

## Technology Stack

- **ML**: Python 3.10, scikit-surprise (SVD), pandas, NumPy
- **API**: Flask (lightweight, hackathon-appropriate)
- **Container**: Docker with `python:3.10-slim` base
- **Cloud**: AWS ECS Fargate, ECR, optional ALB
- **Storage**: Model as `model.pkl` (pickle), movies data in-memory

## Project Structure (Target)

```
KnightRecs/
├── ml-latest/                # MovieLens dataset (already present)
│   ├── ratings.csv           # 33.8M user ratings
│   └── movies.csv            # 86K movie titles + genres
├── src/
│   ├── train.py              # Model training script (SVD with surprise)
│   ├── app.py                # Flask API (GET /recommend?user_id=X&n=5)
│   └── utils.py              # Helper functions (optional)
├── model.pkl                 # Trained SVD model (gitignored)
├── requirements.txt          # flask, pandas, scikit-surprise, numpy
├── Dockerfile                # Container definition
├── .dockerignore             # Exclude ml-latest/ from image (too large)
└── tests/                    # Optional: pytest for API/model
```

## Implementation Workflow

### 1. Model Training (`src/train.py`)
```python
# Load data from ml-latest/ratings.csv and movies.csv
# Use surprise.Dataset and surprise.SVD(n_factors=50)
# Train/test split (80/20), evaluate RMSE
# Save model with pickle.dump(model, 'model.pkl')
```

**Key details**:
- Rating scale: 0.5 to 5.0 stars (surprise Reader)
- Filter to manageable subset if needed (e.g., users with >20 ratings)
- Track `user_movies` dict: userId → list of rated movieIds (for filtering seen movies)

### 2. Flask API (`src/app.py`)
**Endpoint**: `GET /recommend?user_id=<int>&n=<int>`

**Logic**:
1. Load `model.pkl` and `movies.csv` at startup (global variables)
2. For given user, get list of already-rated movies (exclude from recommendations)
3. Predict rating for all unseen movies: `model.predict(user_id, movie_id).est`
4. Sort by predicted rating (descending), return top N
5. Join with movie titles for output

**Response format**:
```json
{
  "user_id": 123,
  "recommendations": [
    {"movieId": 456, "title": "Movie Name (Year)", "predicted_rating": 4.5},
    ...
  ]
}
```

**Critical Flask config**:
- `app.run(host="0.0.0.0", port=5000)` — must bind to 0.0.0.0 for container access
- Error handling: return 404 if user not in dataset

### 3. Containerization (Dockerfile)
```dockerfile
FROM python:3.10-slim
WORKDIR /app

# Install build tools for surprise (requires gcc)
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY necessary files (not ml-latest/ — use .dockerignore)
COPY src/ ./src/
COPY model.pkl .
COPY ml-latest/movies.csv ./ml-latest/movies.csv

EXPOSE 5000
CMD ["python", "src/app.py"]
```

**`.dockerignore`**: Exclude `ml-latest/ratings.csv` and other large files (only need `movies.csv` at runtime)

## AWS Deployment Checklist

### ECR Setup
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag knightrecs:latest <account>.dkr.ecr.us-east-1.amazonaws.com/knightrecs:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/knightrecs:latest
```

### ECS Fargate (via Console)
1. **Cluster**: Create Fargate cluster (e.g., `recsys-cluster`)
2. **Task Definition**: 
   - Image URI from ECR
   - CPU: 0.5 vCPU, Memory: 1 GB (free tier)
   - Port mapping: 5000 TCP
   - Execution role: `ecsTaskExecutionRole`
   - CloudWatch Logs: enable for debugging
3. **Service**: 
   - Launch type: Fargate, 1 task
   - **Networking**: VPC with public subnet, auto-assign public IP = ENABLED
   - Security group: allow inbound TCP 5000
   - Optional: ALB on port 80 → forward to container 5000 (costs vs. direct IP trade-off)

### Testing Deployment
```bash
# Find task public IP in ECS console → Tasks → <task-id> → Networking
curl "http://<TASK-IP>:5000/recommend?user_id=1&n=5"

# Or with ALB DNS:
curl "http://<LB-DNS>/recommend?user_id=1&n=5"
```

## Coding Conventions

- **Python Style**: PEP 8, type hints where helpful (e.g., `def recommend(user_id: int, n: int) -> list`)
- **Comments**: Write clear docstrings for functions to guide Copilot
- **Error Handling**: Check for missing users, empty results
- **Performance**: Pre-load model and movies at startup (not per-request)
- **Dataset Sampling**: For faster iteration, consider sampling 1M ratings during development

## Copilot Usage Tips

1. **Model Training Prompt**:
   ```python
   # Train a collaborative filtering SVD model on MovieLens ratings
   # Use surprise library: Reader, Dataset, SVD(n_factors=50)
   # Split 80/20, evaluate RMSE, save with pickle
   ```

2. **Recommendation Logic Prompt**:
   ```python
   def get_recommendations(user_id, model, movies_df, user_movies_dict, n=5):
       """
       Generate top-N movie recommendations for a user.
       Exclude movies the user has already rated.
       Return list of dicts with movieId, title, predicted_rating.
       """
   ```

3. **Dockerfile Prompt**: Start with comment `# Dockerfile for Flask app with scikit-surprise`

## Common Pitfalls & Fixes

1. **Large Docker image**: Exclude `ml-latest/ratings.csv` (3GB+) from container — only need `movies.csv`
2. **Flask not accessible**: Ensure `host="0.0.0.0"` in `app.run()`
3. **ECS task failing**: Check CloudWatch logs; common issues: missing model.pkl, OOM (increase memory), execution role permissions
4. **Cold start for new users**: Return popular movies or error message for users not in training data
5. **Slow predictions**: Cache top recommendations per user, or pre-compute at training time

## Demo Preparation (Hackathon)

- **Live demo**: Hit API with 2-3 user IDs, show JSON output
- **Diagram**: Draw flow from data → SVD training → Flask → AWS → user query
- **Talking points**: 
  - "Used Copilot to accelerate Flask API and training code"
  - "33M ratings dataset, SVD matrix factorization"
  - "Deployed on AWS Fargate serverless containers (free tier)"
- **Optional frontend**: Simple HTML/JS page that calls API and displays movies

## Key Metrics

- **Model**: RMSE < 1.0 on test set
- **API**: Response time < 2s for top-10 recommendations
- **Cost**: Stay within AWS free tier (Fargate 750 hours/month first year)
