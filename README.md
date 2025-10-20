# KnightRecs
A containerized movie recommender system using SVD Collaborative Filtering, deployed on AWS ECS/Fargate.

Built for **KnightHacks 8** hackathon (Oct 24-26, 2025).

## Overview

KnightRecs is an AI-powered movie recommendation system that uses **Singular Value Decomposition (SVD)** matrix factorization to provide personalized movie recommendations. The system is trained on the **MovieLens dataset** (33.8M ratings, 86K movies, 331K users) and served via a REST API.

### Features

- ✨ **Collaborative Filtering**: SVD-based matrix factorization for accurate recommendations
- 🚀 **RESTful API**: Simple Flask API with JSON responses
- 🐳 **Containerized**: Docker-ready for easy deployment
- ☁️ **Cloud-Native**: Designed for AWS ECS/Fargate deployment
- 📊 **Real Dataset**: Trained on MovieLens `ml-latest` dataset

### Tech Stack

- **ML/Data**: Python 3.13, NumPy, pandas, scipy, scikit-learn
- **API**: Flask 3.x
- **Containerization**: Docker
- **Cloud**: AWS ECS/Fargate, ECR

## Quick Start

### Prerequisites

- Python 3.13+ (or 3.10+)
- Docker (for containerization)
- AWS CLI (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/eugenechevski/KnightRecs.git
   cd KnightRecs
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Train the model**
   ```bash
   python src/train.py
   ```
   
   This will:
   - Load the MovieLens dataset from `ml-latest/`
   - Sample 1M ratings for faster training (configurable)
   - Train an SVD model with 50 latent factors
   - Save `model.pkl` and `user_rated_items.pkl`
   - Output: RMSE ~2.77, MAE ~2.53 on test set

4. **Run the API locally**
   ```bash
   PORT=8000 python src/app.py
   ```

5. **Test the API**
   ```bash
   # Health check
   curl http://localhost:8000/
   
   # Get recommendations for user 76234
   curl "http://localhost:8000/recommend?user_id=76234&n=5"
   ```

### API Endpoints

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "service": "KnightRecs",
  "status": "running",
  "version": "1.0.0"
}
```

#### `GET /recommend`
Get personalized movie recommendations for a user.

**Parameters:**
- `user_id` (required): User ID from the training dataset
- `n` (optional): Number of recommendations (default: 5, max: 100)

**Example:**
```bash
curl "http://localhost:8000/recommend?user_id=76234&n=10"
```

**Response:**
```json
{
  "user_id": 76234,
  "count": 10,
  "recommendations": [
    {
      "movieId": 4963,
      "title": "Ocean's Eleven (2001)",
      "genres": "Crime|Thriller",
      "predicted_rating": 3.52
    }
  ]
}
```

## Docker Deployment

### Build the Docker Image

```bash
# Build image
docker build -t knightrecs:latest .

# Run container
docker run -p 5000:5000 knightrecs:latest
```

### Test Containerized API

```bash
curl "http://localhost:5000/recommend?user_id=76234&n=5"
```

## AWS ECS/Fargate Deployment

### 1. Push to Amazon ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository (if not exists)
aws ecr create-repository --repository-name knightrecs --region us-east-1

# Tag and push image
docker tag knightrecs:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/knightrecs:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/knightrecs:latest
```

### 2. Deploy to ECS Fargate

**Via AWS Console:**

1. **Create ECS Cluster** (Fargate type)
2. **Create Task Definition:**
   - Container image: ECR URI
   - CPU: 0.5 vCPU, Memory: 1 GB
   - Port mapping: 5000 TCP
   - Execution role: `ecsTaskExecutionRole`
3. **Create Service:**
   - Launch type: Fargate
   - Tasks: 1
   - Networking: Enable auto-assign public IP
   - Optional: Add Application Load Balancer

### 3. Test Deployment

```bash
# Get task public IP from ECS console
curl "http://<TASK-IP>:5000/recommend?user_id=76234&n=5"

# Or with ALB:
curl "http://<ALB-DNS>/recommend?user_id=76234&n=5"
```

## Project Structure

```
KnightRecs/
├── ml-latest/              # MovieLens dataset (33.8M ratings)
│   ├── ratings.csv
│   └── movies.csv
├── src/
│   ├── train.py           # SVD model training script
│   └── app.py             # Flask API service
├── model.pkl              # Trained SVD model (gitignored)
├── user_rated_items.pkl   # User rating history (gitignored)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── .dockerignore          # Exclude large files from image
└── .github/
    └── copilot-instructions.md  # AI agent guidelines
```

## Model Details

### Algorithm: SVD Matrix Factorization

The recommender uses **Singular Value Decomposition** to factorize the user-item rating matrix into three matrices:
- **U**: User latent factor matrix (users × k)
- **Σ**: Diagonal matrix of singular values (k × k)
- **V^T**: Item latent factor matrix (k × movies)

**Prediction:** `rating = U[user] × Σ × V^T[:, movie]`

### Training Configuration

- **Dataset**: MovieLens `ml-latest` (sampled to 1M ratings for speed)
- **Latent factors**: 50
- **Train/Test split**: 80/20
- **Performance**: RMSE 2.77, MAE 2.53

### Collaborative Filtering

The model learns latent features from user rating patterns to predict preferences for unseen movies. It filters out already-rated movies and returns top-N recommendations sorted by predicted rating.

## Development

### Training with Full Dataset

Edit `src/train.py` and comment out the sampling line:

```python
# ratings_df = sample_data(ratings_df, sample_size=1_000_000)
```

Then retrain:
```bash
python src/train.py
```

### Adjusting Model Parameters

In `src/train.py`, modify:
```python
k = 50  # Number of latent factors (higher = more complex model)
```

## Cost Optimization (AWS Free Tier)

- **ECS Fargate**: 750 hours/month free (first year)
- **ECR**: 500 MB storage/month free (first year)
- **Data Transfer**: 1 GB/month free
- **Recommended**: Run 1 task with 0.5 vCPU, 1 GB RAM

## Troubleshooting

### Port 5000 Already in Use

On macOS, AirPlay Receiver uses port 5000. Solutions:
1. Disable AirPlay Receiver in System Settings
2. Use different port: `PORT=8000 python src/app.py`

### Model Not Found

Run training first:
```bash
python src/train.py
```

### Docker Image Too Large

Ensure `.dockerignore` excludes large files:
```
ml-latest/ratings.csv    # 3GB+ file
ml-latest/tags.csv
```

## Contributing

Built for KnightHacks 8 hackathon. Contributions welcome!

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **MovieLens Dataset**: F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4.
- **KnightHacks**: UCF's premier hackathon

## Authors

- Eugene Chevski - [@eugenechevski](https://github.com/eugenechevski)

---

**KnightRecs** - AI-Powered Movie Recommendations 🎬✨
