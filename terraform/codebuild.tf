resource "aws_s3_bucket_object" "buildspec_file" {
  bucket = aws_s3_bucket.aiminnews.id
  key    = "codebuild/buildspec.yml"
  source = "files/codebuild/buildspec.yml"
  etag   = filemd5("files/codebuild/buildspec.yml")
}

resource "aws_codebuild_project" "build-website" {
  name          = "newsaiimg-${local.environment_map[var.environment]}-codebuild-build-website"
  description   = "To deploy the Hugu site to s3 bucket"
  build_timeout = 30
  logs_config {
    cloudwatch_logs {
      group_name  = "log-group"
      stream_name = "log-stream"
    }
  }
  source {
    type      = "S3"
    location  = "${aws_s3_bucket.aiminnews.bucket}/codebuild/"
    buildspec = "buildspec.yml"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/standard:5.0"
    type         = "LINUX_CONTAINER"
    environment_variable {
      name  = "SOURCE_BUCKET"
      value = aws_s3_bucket.aiminnews.bucket
    }
    environment_variable {
      name  = "DESTINATION_BUCKET"
      value = aws_s3_bucket.website.bucket
    }
    environment_variable {
      name  = "environment"
      value = var.environment
    }
    environment_variable {
      name  = "CDNADDR"
      value = aws_cloudfront_distribution.cdn.domain_name
    }
    environment_variable {
      name  = "CDNID"
      value = aws_cloudfront_distribution.cdn.id
    }
  }
  artifacts {
    type = "NO_ARTIFACTS"
  }
  service_role = aws_iam_role.codebuild_role.arn
}

resource "aws_iam_role" "codebuild_role" {
  name = "codebuild-service-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name = "codebuild-policy"
  role = aws_iam_role.codebuild_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "cloudfront:CreateInvalidation"
        ]
        Resource = [
          aws_s3_bucket.aiminnews.arn,
          "${aws_s3_bucket.aiminnews.arn}/*",
          aws_s3_bucket.website.arn,
          "${aws_s3_bucket.website.arn}/*",
          "arn:aws:logs:*",
          "arn:aws:cloudfront::*"
        ]
      }
    ]
  })
}
