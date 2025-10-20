# KnightRecs - AI Coding Agent Instructions

## Project Overview
KnightRecs is a containerized movie recommendation system using SVD (Singular Value Decomposition) Collaborative Filtering, designed to run on AWS ECS/Fargate with a REST API interface.

## Architecture Guidelines

### Core Components (Expected)
- **Recommendation Engine**: SVD-based collaborative filtering model for movie recommendations
- **API Service**: RESTful API for serving recommendations and managing user interactions
- **Data Pipeline**: Data preprocessing and model training pipeline
- **Infrastructure**: AWS ECS/Fargate containerized deployment

### Technology Stack (Inferred)
- **ML/Data**: Python (likely NumPy, SciPy, scikit-learn for SVD implementation)
- **API**: Python web framework (Flask/FastAPI recommended for microservices)
- **Container**: Docker for containerization
- **Cloud**: AWS ECS/Fargate for orchestration
- **Data Storage**: Consider RDS/DynamoDB for user data, S3 for model artifacts

## Development Workflow

### Project Structure (To Be Established)
```
src/
  ├── api/              # API service code
  ├── models/           # Recommendation algorithms
  ├── data/             # Data processing utilities
  └── utils/            # Shared utilities
tests/                  # Unit and integration tests
docker/                 # Dockerfile(s) and compose files
infrastructure/         # IaC (Terraform/CloudFormation)
data/                   # Sample datasets (gitignored)
requirements.txt        # Python dependencies
```

### Coding Conventions
- **Python Style**: Follow PEP 8; use type hints for function signatures
- **API Design**: RESTful endpoints; use proper HTTP methods and status codes
- **Model Versioning**: Version trained models (e.g., `model_v1.pkl`)
- **Configuration**: Use environment variables for AWS credentials and config
- **Error Handling**: Include proper exception handling for API and ML operations

### AWS Deployment Patterns
- **Container Registry**: Push images to Amazon ECR
- **Task Definitions**: Define ECS tasks with appropriate CPU/memory allocation
- **Service Discovery**: Use ALB for API routing
- **Secrets**: Store credentials in AWS Secrets Manager
- **Logging**: Configure CloudWatch for container logs

### Testing Strategy
- **Unit Tests**: Test recommendation algorithms independently
- **Integration Tests**: Test API endpoints with mock data
- **Model Tests**: Validate SVD model performance metrics (RMSE, MAE)
- **Load Tests**: Verify API performance under expected traffic

### Data & Model Guidelines
- **Dataset**: Use MovieLens dataset or similar for training
- **Training**: Implement offline batch training for SVD model
- **Evaluation**: Track metrics like precision@k, recall@k, RMSE
- **Cold Start**: Plan for handling new users/items without ratings
- **Caching**: Cache frequent recommendations to reduce latency

## Key Commands (To Be Defined)
```bash
# Local development
python -m src.api.main              # Run API locally
python -m src.models.train          # Train recommendation model

# Docker
docker build -t knightrecs:latest . # Build container
docker-compose up                   # Run full stack locally

# Testing
pytest tests/                       # Run test suite
pytest tests/api --cov              # API tests with coverage

# AWS deployment
aws ecr get-login-password | docker login ...  # ECR login
docker push <ecr-repo>/knightrecs:latest       # Push image
aws ecs update-service ...                      # Update service
```

## Important Notes
- This is an early-stage project; structure may evolve
- Prioritize API design and model performance metrics early
- Consider scalability: SVD training can be computationally expensive
- Plan for incremental model updates vs. full retraining
