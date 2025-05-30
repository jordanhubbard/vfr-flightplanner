#!/bin/bash
# Docker container management script for Weather Forecasts application

# Default values
PORT=5050
IMAGE_NAME="weather-forecasts"
CONTAINER_NAME="weather-forecasts-container"

# Help function
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  run         Run the Docker container"
    echo "  stop        Stop the Docker container"
    echo "  restart     Restart the Docker container"
    echo "  logs        Show container logs"
    echo "  clean       Remove container and image"
    echo "  help        Show this help message"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT    Port to expose (default: 5050)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 run --port 8080"
}

# Parse command line arguments
COMMAND=$1
shift

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    build)
        echo "Building Docker image: $IMAGE_NAME"
        docker build -t $IMAGE_NAME .
        ;;
    run)
        echo "Running Docker container on port $PORT"
        # Stop existing container if it exists
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        
        # Run new container
        docker run -d \
            --name $CONTAINER_NAME \
            -p $PORT:$PORT \
            -e PORT=$PORT \
            --env-file .env \
            $IMAGE_NAME
        
        echo "Container started. Access the application at http://localhost:$PORT"
        ;;
    stop)
        echo "Stopping Docker container"
        docker stop $CONTAINER_NAME
        ;;
    restart)
        echo "Restarting Docker container"
        docker restart $CONTAINER_NAME
        ;;
    logs)
        echo "Showing container logs (press Ctrl+C to exit)"
        docker logs -f $CONTAINER_NAME
        ;;
    clean)
        echo "Removing container and image"
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        docker rmi $IMAGE_NAME 2>/dev/null || true
        echo "Clean completed"
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
