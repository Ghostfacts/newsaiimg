resource "aws_s3_bucket" "aiminnews" {
  # checkov:skip=CKV2_AWS_62
  # checkov:skip=CKV_AWS_18
  # checkov:skip=CKV_AWS_144
  # checkov:skip=CKV_AWS_21
  # checkov:skip=CKV2_AWS_61
  # checkov:skip=CKV_AWS_145
  bucket = "aiminnews"
  tags = {
    Name        = "aiminnews"
    Environment = "Dev"
  }
}

 resource "aws_s3_bucket_public_access_block" "blockpublic" {
  bucket = aws_s3_bucket.aiminnews.id
  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
 }