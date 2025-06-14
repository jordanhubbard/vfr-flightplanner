group "default" {
  targets = ["web"]
}

target "web" {
  context = "."
  dockerfile = "Dockerfile"
  tags = [
    "weather-forecasts:latest"
  ]
  cache-from = ["type=registry,ref=weather-forecasts:buildcache"]
  cache-to = ["type=inline"]
  platforms = ["linux/amd64"]
  args = {
    BUILDKIT_INLINE_CACHE = 1
  }
  output = ["type=docker"]
}
