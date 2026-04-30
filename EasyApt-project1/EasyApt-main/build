#!/bin/bash

################################################################################
# EasyApt Healthcare Scheduling System - Build Script
# 
# This script automates the complete build and deployment process including:
# - Environment setup
# - Dependency installation
# - Database initialization
# - Testing
# - Application startup
#
# Usage:
#   ./build.sh [command]
#
# Commands:
#   setup       - Initial project setup (install dependencies)
#   test        - Run integration tests
#   dev         - Start development server
#   deploy      - Deploy to production (cloud)
#   clean       - Clean build artifacts
#   help        - Show this help message
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/venv"

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

################################################################################
# Build Commands
################################################################################

setup() {
    print_header "EasyApt Build System - Initial Setup"
    
    # Check prerequisites
    print_info "Checking prerequisites..."
    check_command python3
    check_command pip3
    print_success "All prerequisites installed"
    
    # Create Python virtual environment
    print_info "Creating Python virtual environment..."
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists, skipping creation"
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    print_success "Pip upgraded"
    
    # Install Python dependencies
    print_info "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt --quiet
    print_success "Python dependencies installed"
    
    # Install additional dependencies not in requirements.txt
    print_info "Installing additional dependencies..."
    pip install pyotp qrcode pillow pytest pytest-asyncio --quiet
    print_success "Additional dependencies installed"
    
    # Check database
    print_info "Checking database..."
    if [ -f "easyapt.db" ]; then
        print_success "Database exists: $(du -h easyapt.db | cut -f1)"
    else
        print_warning "Database not found - will be created on first run"
    fi
    
    # Check .env file
    print_info "Checking environment configuration..."
    if [ -f ".env" ]; then
        print_success ".env file exists"
    else
        print_error ".env file not found! Please create one based on .env.example"
        exit 1
    fi
    
    print_header "Setup Complete!"
    print_success "Environment is ready for development"
    echo ""
    print_info "Next steps:"
    echo "  ./build.sh test   - Run tests"
    echo "  ./build.sh dev    - Start development server"
}

run_tests() {
    print_header "Running Integration Tests"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if pytest is installed
    if ! python -m pytest --version &> /dev/null; then
        print_error "pytest not installed. Run './build.sh setup' first"
        exit 1
    fi
    
    # Run tests
    print_info "Executing test suite..."
    python -m pytest tests/test_integration.py -v
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

start_dev() {
    print_header "Starting Development Server"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if backend is already running
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Backend already running on port 8000"
        read -p "Kill existing process and restart? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pkill -f uvicorn
            sleep 2
        else
            exit 0
        fi
    fi
    
    # Start backend
    print_info "Starting FastAPI backend on http://localhost:8000"
    print_info "API documentation: http://localhost:8000/docs"
    print_info "Press Ctrl+C to stop"
    echo ""
    
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

deploy_production() {
    print_header "Production Deployment"
    
    print_warning "This will deploy to production server"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Check if server IP is configured
    if [ -z "$DEPLOY_SERVER" ]; then
        print_error "DEPLOY_SERVER environment variable not set"
        print_info "Set it with: export DEPLOY_SERVER=root@192.241.146.169"
        exit 1
    fi
    
    print_info "Deploying to: $DEPLOY_SERVER"
    
    # Create deployment package
    print_info "Creating deployment package..."
    cd "$PROJECT_ROOT"
    zip -r deploy.zip . -x "*/venv/*" "*/__pycache__/*" "*.pyc" "*.git/*" > /dev/null
    print_success "Deployment package created"
    
    # Upload to server
    print_info "Uploading to server..."
    scp deploy.zip "$DEPLOY_SERVER:/root/"
    print_success "Upload complete"
    
    # Deploy on server
    print_info "Deploying on server..."
    ssh "$DEPLOY_SERVER" << 'EOF'
cd /root
unzip -o deploy.zip -d EasyApt-deploy
cd EasyApt-deploy/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyotp qrcode pillow
systemctl restart easyapt
EOF
    
    print_success "Deployment complete!"
    print_info "Backend running at: http://$(echo $DEPLOY_SERVER | cut -d'@' -f2):8000"
    
    # Cleanup
    rm deploy.zip
}

clean() {
    print_header "Cleaning Build Artifacts"
    
    cd "$BACKEND_DIR"
    
    # Remove Python cache
    print_info "Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    print_success "Python cache cleaned"
    
    # Remove test cache
    print_info "Removing test cache..."
    rm -rf .pytest_cache
    print_success "Test cache cleaned"
    
    # Optionally remove virtual environment
    if [ -d "venv" ]; then
        read -p "Remove virtual environment? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_success "Virtual environment removed"
        fi
    fi
    
    print_success "Clean complete"
}

show_help() {
    cat << EOF
EasyApt Build System

Usage: ./build.sh [command]

Commands:
    setup       Initial project setup - install all dependencies
    test        Run integration test suite
    dev         Start development server (localhost:8000)
    deploy      Deploy to production server
    clean       Remove build artifacts and cache files
    help        Show this help message

Examples:
    ./build.sh setup        # First time setup
    ./build.sh test         # Run tests before committing
    ./build.sh dev          # Start local development
    ./build.sh deploy       # Deploy to cloud server

Environment Variables:
    DEPLOY_SERVER    SSH connection string (e.g., root@192.241.146.169)

For more information, see README.md
EOF
}

################################################################################
# Main Script Entry Point
################################################################################

# Check if command provided
if [ $# -eq 0 ]; then
    print_error "No command specified"
    echo ""
    show_help
    exit 1
fi

# Execute command
case "$1" in
    setup)
        setup
        ;;
    test)
        run_tests
        ;;
    dev)
        start_dev
        ;;
    deploy)
        deploy_production
        ;;
    clean)
        clean
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
