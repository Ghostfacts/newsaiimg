resource "aws_s3_bucket" "aiminnews" {
  #checkov:skip=CKV_AWS_20:The bucket is a public static content host
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