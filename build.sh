#!/bin/bash
# Build script for Vercel deployment

# Exit on any error
set -e

# Show commands being executed
set -x

echo "Starting build process..."

# Navigate to frontend directory
cd frontend || exit 1

# Install dependencies
echo "Installing dependencies..."
npm install || { echo "npm install failed"; exit 1; }

# Build the project
echo "Building the project..."
npm run build || { echo "npm run build failed"; exit 1; }

echo "Build complete!"

# Verify dist directory exists
if [ ! -d "dist" ]; then
  echo "Error: dist directory not found after build"
  exit 1
fi

echo "Build successful - dist directory created"