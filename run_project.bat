@echo off
echo ==============================================================================
echo                 OLIST E-COMMERCE END-TO-END PIPELINE LAUNCHER
echo ==============================================================================
echo.

:: Check if .env file exists
if not exist .env (
    echo [ERROR] The .env file was not found!
    echo Please copy .env.example to .env and fill in your Kaggle API credentials.
    echo.
    pause
    exit /b 1
)

echo [1/3] Building and starting database containers...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker Compose. Make sure Docker Desktop is running.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Executing ETL Pipeline inside the container...
echo Logging progress in real-time (press Ctrl+C to exit log tailing, pipeline continues):
echo.
docker compose logs -f etl

echo.
echo [3/3] Running Data Ingestion Verification...
echo.
docker compose run --rm etl python src/verify.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Verification failed! One or both databases might be empty.
) else (
    echo.
    echo [SUCCESS] Verification complete. All database systems are healthy!
)

echo.
echo ==============================================================================
echo Execution complete. Database GUI managers are now active:
echo  - PostgreSQL pgAdmin 4: http://localhost:8082
echo  - MongoDB Express:    http://localhost:8081
echo ==============================================================================
echo.
pause
