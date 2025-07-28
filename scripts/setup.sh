#!/bin/sh
# Basic setup for development environment
set -e

cp -n .env.example .env || true
mkdir -p logs

echo "Environment initialized"
