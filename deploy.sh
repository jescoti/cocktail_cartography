#!/bin/bash

# Deployment script for Cocktail Cartography to DreamHost
# Usage: ./deploy.sh [username] [hostname]
# Example: ./deploy.sh myuser cocktail-cartography.com

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if username and hostname are provided
if [ $# -lt 2 ]; then
    echo -e "${YELLOW}Usage: $0 <username> <hostname>${NC}"
    echo "Example: $0 myuser cocktail-cartography.com"
    exit 1
fi

USERNAME=$1
HOSTNAME=$2
REMOTE_DIR="~/${HOSTNAME}/"

echo -e "${GREEN}Deploying Cocktail Cartography to DreamHost...${NC}"
echo "User: $USERNAME"
echo "Host: $HOSTNAME"
echo "Remote Directory: $REMOTE_DIR"
echo ""

# Check if public directory exists
if [ ! -d "public" ]; then
    echo -e "${RED}Error: public/ directory not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Confirm deployment
read -p "Do you want to continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -q ${USERNAME}@${HOSTNAME} exit; then
    echo -e "${GREEN}SSH connection successful!${NC}"
else
    echo -e "${RED}SSH connection failed. Please check your credentials.${NC}"
    exit 1
fi

# Deploy using rsync
echo -e "${YELLOW}Syncing files to DreamHost...${NC}"
rsync -avz --delete \
    --exclude '.DS_Store' \
    --exclude 'Thumbs.db' \
    public/ ${USERNAME}@${HOSTNAME}:${REMOTE_DIR}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"
    echo ""
    echo "Your site should now be live at:"
    echo "  https://${HOSTNAME}"
    echo ""
    echo "If the site doesn't appear:"
    echo "  1. Clear your browser cache"
    echo "  2. Wait a few minutes for DNS propagation"
    echo "  3. Check the DreamHost panel for domain configuration"
else
    echo -e "${RED}✗ Deployment failed!${NC}"
    echo "Please check the error messages above."
    exit 1
fi