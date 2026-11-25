# Configuration Directory

This directory contains environment and configuration templates for different deployment stages.

## Files

- `development.env` - Development environment configuration template
- Component-specific `.env.example` files are located in their respective directories

## Setup Instructions

### Backend Configuration

1. Navigate to the `backend/` directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your Supabase credentials and database URL

### Frontend Configuration

1. Navigate to the `frontend/` directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your Supabase details and API URL

### Sensor Simulator Configuration

1. Navigate to the `sensor_simulator/` directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Configure sensor parameters and backend URL

## Important Notes

- Never commit `.env` files containing credentials
- Use `.env.example` files as templates with placeholder values
- Each `.env` file is listed in `.gitignore` for security
- Different environments may require different configuration values
