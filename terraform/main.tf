module "news_api_layer" {
  source = "./modules/lambda_layer_python"
  layer_name = "newsapi-test"
  pythonversion = 3.10
  modules = [
    "newsapi==0.1.1",
    "newsapi-python==0.2.7",
    "beautifulsoup4==4.12.3",
    "requests==2.31.0"
  ]
}
