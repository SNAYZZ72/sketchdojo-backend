# SketchDojo Docker Setup

This directory contains the Docker configuration for running the SketchDojo backend in a containerized environment.

## Files Overview

- `Dockerfile`: Defines the container image for the SketchDojo backend
- `docker-compose.yml`: Orchestrates the backend service and Redis
- `docker-settings.py`: Custom settings for the Docker environment
- `.dockerignore`: Files to exclude from the Docker build
- `run-docker.ps1`: PowerShell script to simplify Docker operations

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) installed and running
- [Docker Compose](https://docs.docker.com/compose/install/) (comes with Docker Desktop)

## Getting Started

1. Ensure you have API keys for OpenAI and Stability AI
2. Run the setup script which will create a `.env` file in the project root:
   ```powershell
   .\docker\run-docker.ps1
   ```
3. Edit the `.env` file to add your API keys
4. Run the script again to start the containers:
   ```powershell
   .\docker\run-docker.ps1
   ```

## Usage Options

- **Start containers**: `.\run-docker.ps1`
- **Build only**: `.\run-docker.ps1 -BuildOnly`
- **Rebuild containers**: `.\run-docker.ps1 -Rebuild`

## Accessing the Application

Once running, the application will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Security Notes

- The default JWT and secret keys are for development only
- In production, set strong unique values for `SECRET_KEY` and `JWT_SECRET`
- Remember that the API authentication uses JWT tokens with proper UUID handling

## Troubleshooting

If you encounter authentication errors, check:
1. JWT secret configuration in the `.env` file
2. Ensure your client is using the correct API prefix path
3. Verify that API requests include the proper authorization headers

The Docker setup includes fixes for JWT authentication issues, including proper UUID handling and endpoint URL configurations.
