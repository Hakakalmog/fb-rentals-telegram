#!/bin/bash

# Docker management script for Facebook Rentals Telegram Bot
# Location: .github/scripts/docker.sh
# Usage: ./.github/scripts/docker.sh [command]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="fb-rentals-telegram"
BOT_SERVICE="fb-rentals-bot"
OLLAMA_SERVICE="ollama"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Neither 'docker-compose' nor 'docker compose' is available!"
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found!"
        if [ -f ".env.example" ]; then
            echo "Creating .env from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before starting services."
        else
            print_error ".env.example file also not found! Please create .env file manually."
            exit 1
        fi
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service=$1
    local max_wait=${2:-60}
    local count=0

    print_status "Waiting for $service to be ready..."
    while [ $count -lt "$max_wait" ]; do
        if $COMPOSE_CMD ps "$service" | grep -q "Up"; then
            print_success "$service is ready!"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    echo ""
    print_error "$service failed to start within $max_wait seconds"
    return 1
}

case "$1" in
    "build")
        print_status "Building Docker images..."
        check_docker_compose
        $COMPOSE_CMD build --no-cache
        print_success "Docker images built successfully!"
        ;;
    "start"|"up")
        print_status "Starting services..."
        check_docker_compose
        check_env_file
        $COMPOSE_CMD up -d

        # Wait for services to be ready
        wait_for_service $OLLAMA_SERVICE 120
        wait_for_service $BOT_SERVICE 60

        print_success "All services started successfully!"
        echo ""
        print_status "Available commands:"
        echo "  📜 View logs: ./.github/scripts/docker.sh logs"
        echo "  📊 Check status: ./.github/scripts/docker.sh status"
        echo "  🧪 Run test: ./.github/scripts/docker.sh test"
        ;;
    "stop"|"down")
        print_status "Stopping services..."
        check_docker_compose
        $COMPOSE_CMD down
        print_success "Services stopped successfully!"
        ;;
    "restart")
        print_status "Restarting services..."
        check_docker_compose
        $COMPOSE_CMD down
        sleep 2
        $COMPOSE_CMD up -d
        wait_for_service $OLLAMA_SERVICE 120
        wait_for_service $BOT_SERVICE 60
        print_success "Services restarted successfully!"
        ;;
    "logs")
        echo -e "${BLUE}📜 Showing logs for $BOT_SERVICE (press Ctrl+C to exit)...${NC}"
        check_docker_compose
        $COMPOSE_CMD logs -f $BOT_SERVICE
        ;;
    "logs-all")
        echo -e "${BLUE}📜 Showing logs for all services (press Ctrl+C to exit)...${NC}"
        check_docker_compose
        $COMPOSE_CMD logs -f
        ;;
    "status")
        print_status "Service status:"
        check_docker_compose
        $COMPOSE_CMD ps
        echo ""
        print_status "Container resource usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -n 10
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and images!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."
            check_docker_compose
            $COMPOSE_CMD down -v --remove-orphans
            docker system prune -f
            # Remove project-specific images
            docker image rm ${PROJECT_NAME}_${BOT_SERVICE} 2>/dev/null || true
            docker image rm ${PROJECT_NAME}-${BOT_SERVICE} 2>/dev/null || true
            print_success "Cleanup completed!"
        else
            print_status "Cleanup cancelled."
        fi
        ;;
    "shell")
        print_status "Opening shell in $BOT_SERVICE container..."
        check_docker_compose
        $COMPOSE_CMD exec $BOT_SERVICE bash
        ;;
    "shell-ollama")
        print_status "Opening shell in $OLLAMA_SERVICE container..."
        check_docker_compose
        $COMPOSE_CMD exec $OLLAMA_SERVICE bash
        ;;
    "test")
        print_status "Running configuration test..."
        check_docker_compose
        $COMPOSE_CMD exec $BOT_SERVICE python main.py test
        ;;
    "run-once")
        print_status "Running scraper once..."
        check_docker_compose
        $COMPOSE_CMD exec $BOT_SERVICE python main.py once
        ;;
    "pull-model")
        print_status "Pulling LLM model in Ollama..."
        check_docker_compose
        model=${2:-"llama3.1:latest"}
        $COMPOSE_CMD exec $OLLAMA_SERVICE ollama pull "$model"
        print_success "Model $model pulled successfully!"
        ;;
    "backup")
        print_status "Creating backup of data directory..."
        backup_name="backup-$(date +%Y%m%d-%H%M%S)"
        tar -czf "${backup_name}.tar.gz" data/ logs/ browser_data/ .env 2>/dev/null || true
        print_success "Backup created: ${backup_name}.tar.gz"
        ;;
    "update")
        print_status "Updating and restarting services..."
        check_docker_compose
        git pull
        $COMPOSE_CMD build --no-cache
        $COMPOSE_CMD down
        $COMPOSE_CMD up -d
        print_success "Services updated and restarted!"
        ;;
    *)
        echo -e "${PURPLE}🐳 Facebook Rentals Bot - Docker Management${NC}"
        echo -e "${PURPLE}===========================================${NC}"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo -e "${GREEN}Main Commands:${NC}"
        echo "  build          - Build Docker images"
        echo "  start|up       - Start all services"
        echo "  stop|down      - Stop all services"
        echo "  restart        - Restart all services"
        echo "  status         - Show service status and resource usage"
        echo ""
        echo -e "${YELLOW}Monitoring Commands:${NC}"
        echo "  logs           - Show bot logs"
        echo "  logs-all       - Show logs for all services"
        echo "  test           - Run configuration test"
        echo ""
        echo -e "${BLUE}Development Commands:${NC}"
        echo "  shell          - Open shell in bot container"
        echo "  shell-ollama   - Open shell in ollama container"
        echo "  run-once       - Run scraper once"
        echo "  pull-model [model] - Pull LLM model (default: llama3.1:latest)"
        echo ""
        echo -e "${RED}Maintenance Commands:${NC}"
        echo "  clean          - Remove containers, volumes, and images"
        echo "  backup         - Create backup of data, logs, and config"
        echo "  update         - Git pull, rebuild, and restart"
        echo ""
        echo -e "${GREEN}Examples:${NC}"
        echo "  $0 start       # Start the bot"
        echo "  $0 logs        # View logs"
        echo "  $0 test        # Test configuration"
        echo "  $0 pull-model llama3.1:latest  # Pull smaller model"
        exit 1
        ;;
esac
