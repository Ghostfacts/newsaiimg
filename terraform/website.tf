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

  website {
    index_document = "index.html"
    error_document = "error.html"
  }
  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-s3-website"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}


# # S3 Bucket Policy to Allow Public Read Access
# resource "aws_s3_bucket_policy" "website_bucket_policy" {
#   bucket = aws_s3_bucket.website_bucket.id
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect    = "Allow"
#         Principal = "*"
#         Action    = "s3:GetObject"
#         Resource  = "${aws_s3_bucket.website_bucket.arn}/*"
#       }
#     ]
#   })
# }

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

# # Optional: Upload all files from a folder to the S3 bucket
# resource "aws_s3_bucket_object" "website_files" {
#   for_each = fileset("path/to/your/website-folder", "**") # Replace with the path to your folder
#   bucket   = aws_s3_bucket.website_bucket.id
#   key      = each.value
#   source   = "path/to/your/website-folder/${each.value}" # Replace with the path to your folder
# }