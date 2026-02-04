# Deployment Guide

## Prerequisites

### AWS Account Requirements
- Active AWS account
- IAM user with appropriate permissions
- AWS CLI configured (for command-line deployments)

### Required AWS Services
1. **AWS Textract** - Available in your region
2. **AWS Bedrock** - Claude 3.5 Sonnet model access enabled
3. **AWS S3** - For document storage (optional)
4. **AWS Lambda** - For serverless deployment (optional)
5. **AWS DynamoDB** - For result storage (optional)

### IAM Permissions Required

Create an IAM role or user with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-5-sonnet-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Deployment Options

### Option 1: AWS Lambda (Recommended for Sporadic Usage)

#### Step 1: Create Deployment Package

```bash
# Create a clean directory
mkdir lambda-package
cd lambda-package

# Copy source code
cp -r ../src ../config .

# Install dependencies
pip install -r ../requirements.txt -t .

# Create ZIP file
zip -r ../cosentyx-ocr-lambda.zip .
cd ..
```

#### Step 2: Create Lambda Function

**Via AWS Console**:
1. Open AWS Lambda console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `cosentyx-ocr-extractor`
5. Runtime: Python 3.11
6. Architecture: x86_64
7. Click "Create function"

**Via AWS CLI**:
```bash
aws lambda create-function \
  --function-name cosentyx-ocr-extractor \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler src.lambda_handler.lambda_handler \
  --zip-file fileb://cosentyx-ocr-lambda.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{
    AWS_REGION=us-east-1,
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0,
    TEXTRACT_CONFIDENCE_THRESHOLD=0.85,
    LOG_LEVEL=INFO
  }"
```

#### Step 3: Configure Lambda

**Memory**: 512 MB (minimum), 1024 MB (recommended)
**Timeout**: 60 seconds (minimum), 120 seconds (recommended)
**Environment Variables**: Set all required variables from `.env.example`

#### Step 4: Set Up S3 Trigger (Optional)

1. In Lambda console, add trigger
2. Select S3
3. Choose bucket
4. Event type: "All object create events"
5. Prefix (optional): `uploads/`
6. Suffix: `.pdf`

#### Step 5: Create API Gateway (Optional)

For HTTP API access:

```bash
aws apigatewayv2 create-api \
  --name cosentyx-ocr-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:REGION:ACCOUNT_ID:function:cosentyx-ocr-extractor
```

### Option 2: Docker Container (Local or ECS)

#### Step 1: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY config/ ./config/
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "-m", "src.lambda_handler"]
```

#### Step 2: Build Docker Image

```bash
docker build -t cosentyx-ocr-extractor:latest .
```

#### Step 3: Run Locally

```bash
docker run -p 8080:8080 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0 \
  cosentyx-ocr-extractor:latest
```

#### Step 4: Deploy to ECS/Fargate

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag cosentyx-ocr-extractor:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cosentyx-ocr:latest

docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cosentyx-ocr:latest

# Create ECS task definition and service
# (Use AWS Console or CloudFormation)
```

### Option 3: EC2 Instance

#### Step 1: Launch EC2 Instance

- AMI: Amazon Linux 2 or Ubuntu
- Instance Type: t3.medium or larger
- Security Group: Allow SSH (22) and HTTP (80/443)

#### Step 2: Install Dependencies

```bash
# SSH into instance
ssh -i key.pem ec2-user@instance-ip

# Install Python 3.11
sudo yum install python3.11 -y

# Clone repository
git clone https://github.com/hsavaliya702/cosentyx-ocr-extractor.git
cd cosentyx-ocr-extractor

# Install dependencies
pip3.11 install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your values
```

#### Step 3: Run as Service

Create systemd service:

```bash
sudo nano /etc/systemd/system/cosentyx-ocr.service
```

```ini
[Unit]
Description=Cosentyx OCR Extractor
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/cosentyx-ocr-extractor
ExecStart=/usr/bin/python3.11 -m src.lambda_handler
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable cosentyx-ocr
sudo systemctl start cosentyx-ocr
sudo systemctl status cosentyx-ocr
```

## Configuration Management

### Environment Variables

Set all required environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Textract Configuration
export TEXTRACT_CONFIDENCE_THRESHOLD=0.85
export TEXTRACT_MAX_RETRIES=3

# Bedrock Configuration
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
export BEDROCK_MAX_TOKENS=4096
export BEDROCK_TEMPERATURE=0.1

# Application Configuration
export LOG_LEVEL=INFO
export ENABLE_DUPLICATE_CHECK=true
export ENABLE_BEDROCK_VALIDATION=true
```

### Secrets Management

#### AWS Secrets Manager

Store sensitive credentials in Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name cosentyx-ocr-credentials \
  --secret-string '{"AWS_ACCESS_KEY_ID":"xxx","AWS_SECRET_ACCESS_KEY":"xxx"}'
```

Update code to fetch from Secrets Manager:

```python
import boto3
import json

def get_secrets():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='cosentyx-ocr-credentials')
    return json.loads(response['SecretString'])
```

## Monitoring and Logging

### CloudWatch Logs

Lambda automatically logs to CloudWatch. View logs:

```bash
aws logs tail /aws/lambda/cosentyx-ocr-extractor --follow
```

### CloudWatch Metrics

Create custom metrics:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='CosentyxOCR',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': processing_time_ms,
            'Unit': 'Milliseconds'
        }
    ]
)
```

### CloudWatch Alarms

Create alarms for monitoring:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name cosentyx-ocr-errors \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Scaling Considerations

### Lambda Auto-Scaling

Lambda automatically scales. Configure:
- Reserved concurrency: Guarantee capacity
- Provisioned concurrency: Reduce cold starts

### ECS Auto-Scaling

Create auto-scaling policy:

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/cluster-name/service-name \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10
```

## Cost Optimization

### Estimate Costs

Per 1,000 documents:
- Textract: $1.50
- Bedrock: ~$1.00
- Lambda: $0.20 (avg 3 seconds @ 512MB)
- **Total**: ~$2.70 per 1,000 documents

### Reduce Costs

1. **Batch Processing**: Process multiple documents in one Lambda invocation
2. **Caching**: Cache Bedrock responses for similar content
3. **Confidence Thresholds**: Skip Bedrock validation for high-confidence extractions
4. **Reserved Capacity**: For predictable workloads

## Testing Deployment

### Test Lambda Function

```bash
# Create test event
cat > test-event.json << EOF
{
  "document_base64": "$(base64 < examples/sample_forms/EMA-Start-Form_1.pdf)"
}
EOF

# Invoke function
aws lambda invoke \
  --function-name cosentyx-ocr-extractor \
  --payload file://test-event.json \
  response.json

# Check result
cat response.json | jq
```

### Load Testing

Use AWS Load Testing or Artillery:

```bash
artillery quick --count 100 --num 10 https://your-api-endpoint
```

## Troubleshooting

### Common Issues

**Issue**: Textract quota exceeded
**Solution**: Request quota increase or implement rate limiting

**Issue**: Bedrock model not available
**Solution**: Check model ID and region, request model access

**Issue**: Lambda timeout
**Solution**: Increase timeout to 120 seconds or optimize processing

**Issue**: Out of memory
**Solution**: Increase Lambda memory to 1024 MB

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

## Security Best Practices

1. **Use IAM Roles**: Never hardcode credentials
2. **Encrypt at Rest**: Enable S3 bucket encryption
3. **Encrypt in Transit**: Use HTTPS/TLS for all API calls
4. **VPC Configuration**: Run Lambda in VPC for private resources
5. **Regular Updates**: Keep dependencies updated
6. **Audit Logs**: Enable CloudTrail for API audit logs

## Backup and Disaster Recovery

### Backup Strategy

1. **Code**: Version control with Git
2. **Configuration**: Store in Parameter Store or Secrets Manager
3. **Data**: Enable S3 versioning and cross-region replication
4. **Infrastructure**: Use CloudFormation or Terraform

### Disaster Recovery

1. **Multi-Region Deployment**: Deploy in multiple regions
2. **Automated Failover**: Use Route 53 health checks
3. **Regular Testing**: Test DR procedures quarterly
