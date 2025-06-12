<#
.SYNOPSIS
    Deployment script for NexusSentinel FastAPI + PostgreSQL application.

.DESCRIPTION
    This PowerShell script automates the deployment of the NexusSentinel application
    using Docker and Docker Compose on Windows. It handles building, starting,
    stopping, and monitoring the application containers.

.PARAMETER Action
    The action to perform: build, start, stop, restart, status, logs, clean, or help.

.PARAMETER Environment
    The environment to deploy: dev (includes pgAdmin) or prod (API + DB only).

.PARAMETER BuildArgs
    Additional arguments to pass to docker-compose build.

.EXAMPLE
    .\deploy.ps1 -Action build -Environment dev
    Builds the Docker images for development environment.

.EXAMPLE
    .\deploy.ps1 -Action start
    Starts the containers in production mode.

.EXAMPLE
    .\deploy.ps1 -Action logs -Service api
    Shows logs for the API service.

.NOTES
    Author: NexusSentinel Team
    Version: 1.0.0
    Last Updated: 2025-06-12
#>

param (
    [Parameter(Position = 0)]
    [ValidateSet('build', 'start', 'stop', 'restart', 'status', 'logs', 'clean', 'help')]
    [string]$Action = "help",

    [Parameter(Position = 1)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment = "prod",

    [Parameter(Position = 2)]
    [string]$Service,

    [Parameter(Position = 3)]
    [string]$BuildArgs
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ComposeFile = "docker-compose.yml"
$EnvFile = ".env"
$LogFile = "deploy_log.txt"
$ProjectName = "nexussentinel"

# ANSI color codes for Windows Terminal
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Magenta = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

# Function to log messages
function Write-Log {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'SUCCESS')]
        [string]$Level = "INFO"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    # Color based on level
    switch ($Level) {
        "INFO" { Write-Host "$Blue[INFO]$Reset $Message" }
        "WARNING" { Write-Host "$Yellow[WARNING]$Reset $Message" }
        "ERROR" { Write-Host "$Red[ERROR]$Reset $Message" }
        "SUCCESS" { Write-Host "$Green[SUCCESS]$Reset $Message" }
    }
    
    # Append to log file
    Add-Content -Path $LogFile -Value $LogMessage
}

# Function to check prerequisites
function Check-Prerequisites {
    Write-Log "Checking prerequisites..." "INFO"
    
    try {
        # Check Docker
        $dockerVersion = docker --version
        if ($LASTEXITCODE -ne 0) {
            throw "Docker is not installed or not in PATH"
        }
        Write-Log "Docker installed: $dockerVersion" "INFO"
        
        # Check Docker Compose
        $composeVersion = docker compose version
        if ($LASTEXITCODE -ne 0) {
            throw "Docker Compose is not installed or not in PATH"
        }
        Write-Log "Docker Compose installed: $composeVersion" "INFO"
        
        # Check if docker-compose.yml exists
        if (-not (Test-Path $ComposeFile)) {
            throw "Docker Compose file not found: $ComposeFile"
        }
        
        # Check if .env file exists
        if (-not (Test-Path $EnvFile)) {
            Write-Log ".env file not found. Creating a template..." "WARNING"
            @"
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=nexussentinel
DB_SCHEMA=public

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security Configuration
SECRET_KEY=replace_with_secure_generated_key_at_least_32_chars

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development

# pgAdmin (for dev profile)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
"@ | Out-File -FilePath $EnvFile -Encoding utf8
            Write-Log "Created template .env file. Please edit it with your secure credentials." "WARNING"
            Write-Log "Then run this script again." "WARNING"
            return $false
        }
        
        return $true
    }
    catch {
        Write-Log "Prerequisite check failed: $_" "ERROR"
        return $false
    }
}

# Function to build the Docker images
function Build-Images {
    Write-Log "Building Docker images for $Environment environment..." "INFO"
    
    try {
        $profileArg = if ($Environment -eq "dev") { "--profile dev" } else { "" }
        $buildCommand = "docker compose $profileArg build $BuildArgs"
        
        Write-Log "Executing: $buildCommand" "INFO"
        Invoke-Expression $buildCommand
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Docker images built successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Build failed: $_" "ERROR"
        return $false
    }
}

# Function to start the containers
function Start-Containers {
    Write-Log "Starting containers for $Environment environment..." "INFO"
    
    try {
        $profileArg = if ($Environment -eq "dev") { "--profile dev" } else { "" }
        $upCommand = "docker compose $profileArg up -d"
        
        Write-Log "Executing: $upCommand" "INFO"
        Invoke-Expression $upCommand
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker Compose up failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Containers started successfully" "SUCCESS"
        Show-Status
        return $true
    }
    catch {
        Write-Log "Start containers failed: $_" "ERROR"
        return $false
    }
}

# Function to stop the containers
function Stop-Containers {
    Write-Log "Stopping containers..." "INFO"
    
    try {
        $downCommand = "docker compose down"
        
        Write-Log "Executing: $downCommand" "INFO"
        Invoke-Expression $downCommand
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker Compose down failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Containers stopped successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Stop containers failed: $_" "ERROR"
        return $false
    }
}

# Function to restart the containers
function Restart-Containers {
    Write-Log "Restarting containers for $Environment environment..." "INFO"
    
    if (Stop-Containers) {
        Start-Sleep -Seconds 2
        return Start-Containers
    }
    
    return $false
}

# Function to show container status
function Show-Status {
    Write-Log "Checking container status..." "INFO"
    
    try {
        $statusCommand = "docker compose ps"
        
        Write-Log "Container Status:" "INFO"
        Invoke-Expression $statusCommand
        
        # Get API container status to show access URLs
        $apiContainer = docker ps --filter "name=nexussentinel-api" --format "{{.Status}}"
        if ($apiContainer -match "Up") {
            $apiPort = docker port nexussentinel-api 8000
            if ($apiPort) {
                Write-Host "`n$Green[ACCESS INFORMATION]$Reset"
                Write-Host "API is running and accessible at:"
                Write-Host "$Cyan- API:$Reset http://localhost:8000"
                Write-Host "$Cyan- Swagger Docs:$Reset http://localhost:8000/docs"
                Write-Host "$Cyan- Health Check:$Reset http://localhost:8000/health"
            }
        }
        
        # Check if pgAdmin is running (dev environment)
        $pgAdminContainer = docker ps --filter "name=nexussentinel-pgadmin" --format "{{.Status}}"
        if ($pgAdminContainer -match "Up") {
            $pgAdminPort = docker port nexussentinel-pgadmin 80
            if ($pgAdminPort) {
                $port = $pgAdminPort -replace '.*:', ''
                Write-Host "$Cyan- pgAdmin:$Reset http://localhost:$port"
                Write-Host "  Login with credentials from .env file (default: admin@example.com / admin)"
                Write-Host "  Connect to PostgreSQL using host: db, port: 5432, user/pass from .env"
            }
        }
        
        return $true
    }
    catch {
        Write-Log "Status check failed: $_" "ERROR"
        return $false
    }
}

# Function to show container logs
function Show-Logs {
    if ($Service) {
        Write-Log "Showing logs for $Service service..." "INFO"
        $logCommand = "docker compose logs --tail=100 -f $Service"
    }
    else {
        Write-Log "Showing logs for all services..." "INFO"
        $logCommand = "docker compose logs --tail=50 -f"
    }
    
    try {
        Invoke-Expression $logCommand
        return $true
    }
    catch {
        Write-Log "Show logs failed: $_" "ERROR"
        return $false
    }
}

# Function to clean up resources
function Clean-Resources {
    Write-Log "Cleaning up Docker resources..." "INFO"
    
    try {
        $cleanCommand = "docker compose down -v --remove-orphans"
        
        Write-Log "Executing: $cleanCommand" "INFO"
        Invoke-Expression $cleanCommand
        
        Write-Log "Cleaning Docker images..." "INFO"
        docker image prune -f
        
        Write-Log "Cleaning Docker volumes..." "INFO"
        docker volume prune -f
        
        Write-Log "Cleanup completed successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Cleanup failed: $_" "ERROR"
        return $false
    }
}

# Function to show help
function Show-Help {
    Write-Host "`n$Cyan=== NexusSentinel Deployment Script ===$Reset"
    Write-Host "This script helps you deploy and manage the NexusSentinel application using Docker."
    
    Write-Host "`n$Yellow[USAGE]$Reset"
    Write-Host ".\deploy.ps1 [Action] [Environment] [Service] [BuildArgs]"
    
    Write-Host "`n$Yellow[ACTIONS]$Reset"
    Write-Host "$Green build$Reset   - Build Docker images"
    Write-Host "$Green start$Reset   - Start containers"
    Write-Host "$Green stop$Reset    - Stop containers"
    Write-Host "$Green restart$Reset - Restart containers"
    Write-Host "$Green status$Reset  - Show container status"
    Write-Host "$Green logs$Reset    - Show container logs (optionally specify service)"
    Write-Host "$Green clean$Reset   - Clean up all resources (containers, volumes, images)"
    Write-Host "$Green help$Reset    - Show this help message"
    
    Write-Host "`n$Yellow[ENVIRONMENTS]$Reset"
    Write-Host "$Green dev$Reset  - Development environment (includes pgAdmin)"
    Write-Host "$Green prod$Reset - Production environment (API + DB only)"
    
    Write-Host "`n$Yellow[EXAMPLES]$Reset"
    Write-Host ".\deploy.ps1 build dev        - Build images for development"
    Write-Host ".\deploy.ps1 start            - Start containers in production mode"
    Write-Host ".\deploy.ps1 logs api         - Show logs for the API service"
    
    Write-Host "`n$Yellow[REQUIREMENTS]$Reset"
    Write-Host "- Docker Engine"
    Write-Host "- Docker Compose V2"
    Write-Host "- .env file with configuration"
    
    Write-Host "`n$Yellow[NOTES]$Reset"
    Write-Host "- The script creates a log file: $LogFile"
    Write-Host "- Make sure to configure your .env file before starting"
    Write-Host "- Access the API at http://localhost:8000/docs when running"
    Write-Host ""
}

# Main execution
Write-Host "$Cyan=== NexusSentinel Deployment Script ===$Reset"

# Start with prerequisites check for all actions except help
if ($Action -ne "help") {
    $prereqsOk = Check-Prerequisites
    if (-not $prereqsOk) {
        exit 1
    }
}

# Execute the requested action
switch ($Action) {
    "build" {
        Build-Images
    }
    "start" {
        Start-Containers
    }
    "stop" {
        Stop-Containers
    }
    "restart" {
        Restart-Containers
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
    "clean" {
        $confirmation = Read-Host "This will remove all containers, volumes, and images. Are you sure? (y/N)"
        if ($confirmation -eq "y" -or $confirmation -eq "Y") {
            Clean-Resources
        }
        else {
            Write-Log "Cleanup cancelled by user" "INFO"
        }
    }
    "help" {
        Show-Help
    }
    default {
        Write-Log "Unknown action: $Action" "ERROR"
        Show-Help
        exit 1
    }
}
