resource "aws_s3_bucket" "aiminnews" {
  # checkov:skip=CKV2_AWS_62:Dont need Notivcations
  # checkov:skip=CKV_AWS_18:logging not needed
  # checkov:skip=CKV_AWS_144:Cross Region is not needed
  # checkov:skip=CKV_AWS_21:Version control no longer needed
  # checkov:skip=CKV2_AWS_61:Life cycal policy pending
  # checkov:skip=CKV_AWS_145:enc not needed
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