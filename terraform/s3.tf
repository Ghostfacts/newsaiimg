resource "aws_s3_bucket" "aiminnews" {
  bucket = "aiminnews"
  tags = {
    Name        = "aiminnews"
    Environment = "Dev"
  }
}