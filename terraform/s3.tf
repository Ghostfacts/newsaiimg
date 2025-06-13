#Storaing of images
resource "aws_s3_bucket" "aiminnews" { # ts:skip=AC_AWS_0012
  # checkov:skip=CKV2_AWS_62
  # checkov:skip=CKV_AWS_18
  # checkov:skip=CKV_AWS_144
  # checkov:skip=CKV_AWS_21
  # checkov:skip=CKV2_AWS_61
  # checkov:skip=CKV_AWS_145
  bucket = "newsaiimg-${local.environment_map[var.environment]}-s3-imgstorage"
  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-s3-imgstorage"
      datatype = "private"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "imgstorage-blockpublic" {
  bucket                  = aws_s3_bucket.aiminnews.id
  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
  ignore_public_acls      = true
}

# Upload raw website
# Optional: Upload all files from a folder to the S3 bucket
resource "aws_s3_bucket_object" "website_files" {
  for_each = fileset("../website", "**")
  bucket   = aws_s3_bucket.aiminnews.id
  key      = "website/${each.value}"
  source   = "../website/${each.value}"
  etag     = filemd5("../website/${each.value}")
}
