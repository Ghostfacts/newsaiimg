resource "aws_s3_bucket" "website" {
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
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  # checkov:skip=CKV_AWS_54
  # checkov:skip=CKV_AWS_56
  # checkov:skip=CKV_AWS_55
  # checkov:skip=CKV_AWS_53
  bucket                  = aws_s3_bucket.website.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "website_policy" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.website.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn
          }
        }
      }
    ]
  })
}

resource "aws_cloudfront_origin_access_control" "oac" {
  # checkov:skip=CKV2_AWS_32
  name                              = "s3-origin-access-control"
  description                       = "OAC for S3 website"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  # checkov:skip=CKV2_AWS_47
  # checkov:skip=CKV2_AWS_42
  # checkov:skip=CKV_AWS_310
  # checkov:skip=CKV_AWS_174
  # checkov:skip=CKV_AWS_374
  # checkov:skip=CKV_AWS_68
  # checkov:skip=CKV_AWS_86
  # checkov:skip=CKV2_AWS_32
  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
    origin_id                = aws_s3_bucket.website.id
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    target_origin_id       = aws_s3_bucket.website.id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}


##testng
#Upload raw website
# Optional: Upload all files from a folder to the S3 bucket
# resource "aws_s3_bucket_object" "website_files_test" {
#   # checkov:skip=CKV_AWS_186
#   for_each = fileset("files/website", "**") # Replace with the path to your folder
#   bucket   = aws_s3_bucket.website.id
#   key      = each.value
#   source   = each.value # Replace with the path to your folder
# }