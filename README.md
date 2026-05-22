# HazardHub

HazardHub is a Flask + MySQL safety reporting system for hazards and concerns/suggestions. It includes an admin dashboard, employee reporting, a mobile web UI, and AI-assisted priority classification using a Multinomial Naive Bayes model.

## Features
- Hazard and concern reporting with optional photo uploads
- Admin dashboard stats and status tracking
- Certificate folder and file management
- Fire protection inspection logging
- Naive Bayes priority classifier with custom training data
- Separate mobile session cookie support

## Tech stack
- Backend: Flask
- Database: MySQL/MariaDB
- Server: Gunicorn (for production)

## Project structure
- app.py: Flask app, API routes, and Naive Bayes classifier
- hazardhub.sql: Database schema and seed data
- seed.py: Admin account seed/update script
- admin_dashboard.html, login.html: Main UI pages
- mobile_hazardhub.html: Mobile UI
- uploads/: File storage for uploaded images and certificates
- render.yaml / vercel.json: Deployment configs

## Requirements
- Python 3.10+
- MySQL/MariaDB

Install dependencies:
```bash
pip install -r requirements.txt
```

## Database setup
1) Create a database named hazardhub
2) Import the schema:
```bash
mysql -u root -p hazardhub < hazardhub.sql
```
3) Seed or update the admin user:
```bash
python seed.py
```

## Environment variables
The app uses these (defaults shown):
- MYSQL_HOST=localhost
- MYSQL_USER=root
- MYSQL_PASSWORD=
- MYSQL_DB=hazardhub

## Run locally
```bash
python app.py
```
Then visit:
- http://localhost:5000/login
- http://localhost:5000/check
- http://localhost:5000/mobile

## API highlights
- POST /api/login
- GET /api/dashboard/stats
- GET/POST /api/hazards
- GET/POST /api/concerns
- PUT /api/hazards/<id>/status
- PUT /api/concerns/<id>/status
- GET/POST /api/folders and /api/folders/<id>/files
- GET /api/system-info

## Deployment
Render is the recommended target for this app.
1) Create a Render Web Service using render.yaml
2) Provision a hosted MySQL database
3) Set MYSQL_* environment variables in Render
4) Import hazardhub.sql into the database
5) Run python seed.py once to create the admin account

## Notes
- Uploads are stored on the server filesystem under uploads/.
- If you deploy on a serverless platform, use object storage for uploads.