#!/bin/bash
# Build script for Vercel deployment

echo "Starting build process..."

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the project
echo "Building the project..."
npm run build

echo "Build complete!"