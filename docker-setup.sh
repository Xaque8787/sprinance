#!/bin/bash

set -e

echo "========================================"
echo "Docker Setup Script"
echo "========================================"
echo ""

echo "This script will help you set up the Docker environment for your application."
echo ""

read -p "Do you want to set up for (1) Local Development or (2) Production? Enter 1 or 2: " choice

if [ "$choice" == "1" ]; then
    echo ""
    echo "Setting up for LOCAL DEVELOPMENT..."
    echo ""

    if [ ! -f ".env" ]; then
        echo "Creating .env file..."
        cat > .env << EOL
SECRET_KEY=local-development-secret-key-$(openssl rand -hex 16)
TZ=America/New_York
EOL
        echo ".env file created"
    else
        echo ".env file already exists, skipping creation"
    fi

    echo ""
    echo "Creating data directories..."
    mkdir -p data/scheduler data/backups data/reports/daily_report data/reports/tip_report
    # Set permissions for user with UID 1000 (app user in container)
    if [ "$(id -u)" -eq 0 ]; then
        chown -R 1000:1000 data
    else
        sudo chown -R 1000:1000 data || echo "Warning: Could not set ownership. Run script with sudo if you encounter permission issues."
    fi
    chmod -R 755 data
    echo "Data directories created"

    echo ""
    echo "Building Docker image..."
    docker-compose -f docker-compose.local.yml build

    echo ""
    echo "Starting container..."
    docker-compose -f docker-compose.local.yml up -d

    echo ""
    echo "========================================"
    echo "Local Development Setup Complete!"
    echo "========================================"
    echo ""
    echo "Application is running at: http://localhost:5710"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker-compose -f docker-compose.local.yml logs -f"
    echo "  Stop:         docker-compose -f docker-compose.local.yml down"
    echo "  Restart:      docker-compose -f docker-compose.local.yml restart"
    echo ""

elif [ "$choice" == "2" ]; then
    echo ""
    echo "Setting up for PRODUCTION..."
    echo ""

    read -p "Enter your GitHub username: " github_user
    read -p "Enter your application/repository name: " app_name

    if [ -z "$github_user" ] || [ -z "$app_name" ]; then
        echo "ERROR: GitHub username and app name are required!"
        exit 1
    fi

    github_user_lower=$(echo "$github_user" | tr '[:upper:]' '[:lower:]')

    echo ""
    echo "Updating docker-compose.yml..."
    sed -i.bak "s|ghcr.io/YOUR_GITHUB_USERNAME/YOUR_APP_NAME|ghcr.io/$github_user_lower/$app_name|g" docker-compose.yml
    rm -f docker-compose.yml.bak

    if [ ! -f ".env" ]; then
        echo ""
        echo "Creating .env file with secure random secret key..."
        cat > .env << EOL
SECRET_KEY=$(openssl rand -hex 32)
TZ=America/New_York
EOL
        echo ".env file created"
    else
        echo ".env file already exists"
        read -p "Do you want to regenerate the SECRET_KEY? (y/n): " regen
        if [ "$regen" == "y" ]; then
            new_secret=$(openssl rand -hex 32)
            if grep -q "^SECRET_KEY=" .env; then
                sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=$new_secret|g" .env
                rm -f .env.bak
            else
                echo "SECRET_KEY=$new_secret" >> .env
            fi
            echo "New SECRET_KEY generated"
        fi
    fi

    echo ""
    echo "Pulling latest Docker image from GitHub Container Registry..."
    echo "Note: This will fail if you haven't pushed the image yet."
    echo "You can push it by:"
    echo "  1. Committing your changes"
    echo "  2. Pushing to GitHub (triggers GitHub Actions)"
    echo "  3. Waiting for the build to complete"
    echo ""

    read -p "Do you want to pull the image now? (y/n): " pull_choice
    if [ "$pull_choice" == "y" ]; then
        docker-compose pull || echo "Pull failed. You may need to build and push the image first."
    fi

    echo ""
    echo "Creating data directories..."
    mkdir -p data/scheduler data/backups data/reports/daily_report data/reports/tip_report
    # Set permissions for user with UID 1000 (app user in container)
    if [ "$(id -u)" -eq 0 ]; then
        chown -R 1000:1000 data
    else
        sudo chown -R 1000:1000 data || echo "Warning: Could not set ownership. Run script with sudo if you encounter permission issues."
    fi
    chmod -R 755 data
    echo "Data directories created"

    echo ""
    echo "Starting container..."
    docker-compose up -d

    echo ""
    echo "========================================"
    echo "Production Setup Complete!"
    echo "========================================"
    echo ""
    echo "Image: ghcr.io/$github_user_lower/$app_name:latest"
    echo "Application is running at: http://localhost:5710"
    echo ""
    echo "Important:"
    echo "  - Make sure to push your changes to GitHub to trigger the build"
    echo "  - Your SECRET_KEY is stored in .env (keep it secure!)"
    echo "  - Database is persisted in ./data directory"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker-compose logs -f"
    echo "  Stop:         docker-compose down"
    echo "  Restart:      docker-compose restart"
    echo "  Pull updates: docker-compose pull && docker-compose up -d"
    echo ""

else
    echo "Invalid choice. Please run the script again and enter 1 or 2."
    exit 1
fi
