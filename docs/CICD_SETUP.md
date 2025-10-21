# GitHub Actions CI/CD Pipeline Setup

This document provides instructions for setting up the automated CI/CD pipeline for KnightRecs.

## Pipeline Overview

The pipeline consists of 4 jobs that run automatically on push to `main` branch:

1. **Test** - Linting and unit tests
2. **Build** - Docker image build and container testing
3. **Deploy** - Push to AWS ECR and deploy to ECS Fargate
4. **Notify** - Send deployment status notifications (optional)

## Workflow Triggers

- **Push to `main` or `develop`**: Runs test, build, and deploy (main only)
- **Pull Requests to `main`**: Runs tests only
- **Manual trigger**: Can be triggered manually from GitHub Actions tab

## Required GitHub Secrets

To enable the full pipeline, configure these secrets in your GitHub repository:

### AWS Deployment (Required for Deploy Job)

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key | Create IAM user with ECR/ECS permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | From IAM user creation |

**IAM Policy for CI/CD User:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

### Docker Hub (Optional - for public image hosting)

| Secret Name | Description |
|------------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

### Notifications (Optional)

| Secret Name | Description |
|------------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

## AWS Infrastructure Setup

Before the pipeline can deploy, you need to create these AWS resources:

### 1. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name knightrecs \
  --region us-east-1
```

### 2. Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name recsys-cluster \
  --region us-east-1
```

### 3. Create ECS Task Definition

Create a file `task-definition.json`:

```json
{
  "family": "knightrecs-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "knightrecs",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/knightrecs:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/knightrecs",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json
```

### 4. Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name /ecs/knightrecs \
  --region us-east-1
```

### 5. Create ECS Service

```bash
aws ecs create-service \
  --cluster recsys-cluster \
  --service-name knightrecs-service \
  --task-definition knightrecs-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --region us-east-1
```

**Note**: Replace `subnet-xxxxx` and `sg-xxxxx` with your VPC subnet and security group IDs.

## Pipeline Configuration

### Customize Environment Variables

Edit `.github/workflows/ci-cd.yml` to match your AWS setup:

```yaml
env:
  AWS_REGION: us-east-1              # Your AWS region
  ECR_REPOSITORY: knightrecs         # Your ECR repository name
  ECS_CLUSTER: recsys-cluster        # Your ECS cluster name
  ECS_SERVICE: knightrecs-service    # Your ECS service name
  ECS_TASK_DEFINITION: knightrecs-task  # Your task definition family
  CONTAINER_NAME: knightrecs         # Container name in task definition
```

### Disable Deploy Job (Test Locally First)

To test the pipeline without deploying to AWS, comment out the deploy job:

```yaml
  # deploy:
  #   name: Deploy to AWS
  #   runs-on: ubuntu-latest
  #   ...
```

## Pipeline Execution Flow

### On Push to Main

```
┌─────────┐
│  Push   │
│  to     │
│  Main   │
└────┬────┘
     │
     ├──► Test Job (Lint + Unit Tests)
     │         │
     │         ├─ Install dependencies
     │         ├─ Run flake8 linting
     │         └─ Run pytest (if tests exist)
     │
     │    [If test passes]
     │         │
     ├──► Build Job (Docker Image)
     │         │
     │         ├─ Build Docker image
     │         ├─ Test container health
     │         └─ Cache layers
     │
     │    [If build passes]
     │         │
     ├──► Deploy Job (AWS ECS)
     │         │
     │         ├─ Push to ECR
     │         ├─ Update task definition
     │         ├─ Deploy to ECS
     │         └─ Wait for stability
     │
     └──► Notify Job (Status)
              │
              └─ Send notifications
```

### On Pull Request

```
┌──────────┐
│   PR     │
│   to     │
│   Main   │
└────┬─────┘
     │
     └──► Test Job Only
              │
              └─ Quality gates before merge
```

## Testing the Pipeline

### 1. Test Locally First

```bash
# Run linting
pip install flake8
flake8 src/ --count --max-line-length=127

# Build Docker image
docker build -t knightrecs:test .

# Test container
docker run -d -p 5000:5000 --name test knightrecs:test
curl http://localhost:5000/
docker stop test && docker rm test
```

### 2. Create Feature Branch

```bash
git checkout -b feature/test-pipeline
git push -u origin feature/test-pipeline
```

### 3. Create Pull Request

Open a PR to `main` - this will trigger the test job only.

### 4. Merge to Main

After PR approval, merge to `main` to trigger the full pipeline (test → build → deploy).

## Monitoring Pipeline

### View Pipeline Status

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click on a workflow run to see detailed logs

### Check AWS Deployment

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster recsys-cluster \
  --services knightrecs-service \
  --region us-east-1

# Check task logs
aws logs tail /ecs/knightrecs --follow --region us-east-1
```

## Troubleshooting

### Build Fails: "Model not found"

The Docker build requires `model.pkl` and `user_rated_items.pkl`. Solutions:

1. **Train locally before pushing**: Run `python src/train.py` before committing
2. **Add model artifacts to Git LFS**: Track large files with Git LFS
3. **Build model in pipeline**: Add a training step before Docker build (slow)

**Recommended**: Use option 1 or 2 for hackathon demo.

### Deploy Fails: "Task definition not found"

Create the initial task definition manually (see AWS Infrastructure Setup above).

### Container Health Check Fails

Increase sleep time in the build job:

```yaml
# Wait for container to be healthy
sleep 15  # Increase from 10 to 15 seconds
```

### AWS Credentials Invalid

1. Verify IAM user has correct permissions
2. Check secrets are correctly set in GitHub
3. Test credentials locally:

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
aws sts get-caller-identity
```

## Cost Optimization

### Free Tier Limits

- **GitHub Actions**: 2,000 minutes/month (free for public repos)
- **ECR Storage**: 500 MB free (first 12 months)
- **ECS Fargate**: 750 hours/month free (first 12 months)

### Reduce Pipeline Costs

1. **Disable deploy on every push**: Only deploy on releases
2. **Use pull-based deployment**: Deploy manually when needed
3. **Cache dependencies**: Already configured with `cache: 'pip'`

## Advanced Configuration

### Deploy Only on Tag/Release

Change the deploy job condition:

```yaml
deploy:
  if: startsWith(github.ref, 'refs/tags/v')
```

Then create releases:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Add Slack Notifications

Uncomment and configure in the notify job:

```yaml
- name: Deployment Success Notification
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"✅ KnightRecs deployed successfully!"}'
```

### Multi-Environment Deployment

Create separate workflows for `staging` and `production`:

- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`

## Security Best Practices

1. **Never commit secrets**: Use GitHub Secrets for sensitive data
2. **Use IAM roles**: Prefer temporary credentials over access keys
3. **Scan Docker images**: Add security scanning step
4. **Rotate credentials**: Update AWS keys regularly
5. **Limit IAM permissions**: Follow principle of least privilege

## Summary

✅ **Pipeline Created**: `.github/workflows/ci-cd.yml`  
✅ **Jobs Configured**: Test → Build → Deploy → Notify  
✅ **AWS Ready**: ECR push and ECS deployment  
⚠️ **Setup Required**: GitHub secrets and AWS infrastructure

**Next Steps**:
1. Configure GitHub secrets (AWS credentials)
2. Create AWS infrastructure (ECR, ECS cluster, task definition)
3. Train model locally (`python src/train.py`)
4. Push to trigger pipeline!

For questions or issues, refer to GitHub Actions logs and AWS CloudWatch.
