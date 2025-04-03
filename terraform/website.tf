# Create a CloudFront Origin Access Identity (OAI)
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for CloudFront to access S3 bucket"
}

# S3 Bucket for Static Website Hosting
resource "aws_s3_bucket" "website_bucket" {
  # checkov:skip=CKV2_AWS_62
  # checkov:skip=CKV_AWS_18
  # checkov:skip=CKV_AWS_144
  # checkov:skip=CKV_AWS_21
  # checkov:skip=CKV2_AWS_61
  # checkov:skip=CKV_AWS_145
  # checkov:skip=CKV_AWS_20
  # checkov:skip=CKV_AWS_86
  bucket = "newsaiimg-${local.environment_map[var.environment]}-s3-website"
  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-s3-website"
    }
  )
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  # checkov:skip=CKV_AWS_54
  # checkov:skip=CKV_AWS_56
  # checkov:skip=CKV_AWS_55
  # checkov:skip=CKV_AWS_53

  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "website_policy" {
  statement {
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path]

    }
    actions = [
      "s3:GetObject",
    ]
    resources = [
      aws_s3_bucket.website_bucket.arn,
      "${aws_s3_bucket.website_bucket.arn}/*"
    ]
  }
}

resource "aws_s3_bucket_policy" "website_policy" {
  bucket = aws_s3_bucket.website_bucket.id
  policy = data.aws_iam_policy_document.website_policy.json
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  # checkov:skip=CKV_AWS_68
  # checkov:skip=CKV_AWS_174
  # checkov:skip=CKV_AWS_310
  # checkov:skip=CKV2_AWS_42
  # checkov:skip=CKV2_AWS_47
  # checkov:skip=CKV2_AWS_32
  # checkov:skip=CKV_AWS_86
  origin {
    domain_name = aws_s3_bucket.website_bucket.website_endpoint
    origin_id   = "S3-${aws_s3_bucket.website_bucket.id}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.website_bucket.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100"

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # logging_config {
  #   bucket = "${aws_s3_bucket.aiminnews.bucket}.s3.amazonaws.com"
  #   prefix = "cloudfront-logs/"
  # }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US", "CA", "GB", "DE"]
    }
  }
  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-cdn-website"
    }
  )
}

output "s3_website_url" {
  description = "The URL of the S3 bucket website"
  value       = aws_s3_bucket.website_bucket.website_endpoint
}

output "cloudfront_url" {
  description = "The URL of the CloudFront distribution"
  value       = aws_cloudfront_distribution.cdn.domain_name
}
