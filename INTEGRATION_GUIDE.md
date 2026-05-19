# Windshield Dashboard - Integration Guide

Complete step-by-step instructions to integrate the dashboard into your FastAPI backend and Angular frontend.

---

## 📋 TABLE OF CONTENTS

1. [Backend Integration (FastAPI)](#backend-integration-fastapi)
2. [Frontend Integration (Angular)](#frontend-integration-angular)
3. [Configuration & Environment](#configuration--environment)
4. [Testing & Validation](#testing--validation)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 BACKEND INTEGRATION (FastAPI)

### Step 1: Verify Backend Files Are in Place

Your backend directory should now contain:

```
backend/
├── app.py
├── config.py
├── database.py
├── models.py
├── requirements.txt
├── dashboard_router.py          ← NEW FILE
├── measurement.py
├── evaluation.py
└── ...other files
```

### Step 2: Update `backend/app.py` to Mount Dashboard Router

Open **`backend/app.py`** and find the section where routers are imported and included. Add these two lines:

**Add the import** (near the top with other imports):

```python
from dashboard_router import router as dashboard_router
```

**Mount the router** (in the FastAPI initialization section, after other router includes):

```python
app.include_router(dashboard_router)
```

**Example location in app.py:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dashboard_router import router as dashboard_router  # ← ADD THIS

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(dashboard_router)  # ← ADD THIS

@app.on_event("startup")
async def startup_event():
    # ...existing code
```

### Step 3: Verify Database Connection

The dashboard router requires:
- SQLAlchemy ORM configured in `database.py`
- MySQL connection string in environment variables or `config.py`
- `WindshieldTest` model defined in `models.py`

**Verify `database.py` exports `get_db`:**

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 4: Rebuild Backend Docker Image

If running in Docker, rebuild with the new router:

```bash
docker-compose up -d --build backend
```

Or if running locally:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Verify Backend is Running

Check that the backend started without errors:

```bash
# Docker logs
docker-compose logs backend

# Or local: should see "Uvicorn running on http://0.0.0.0:8000"
```

---

## 🎨 FRONTEND INTEGRATION (Angular)

### Step 1: Verify Frontend Files Are in Place

Your frontend directory should now contain:

```
windshield-tester/
├── src/
│   └── app/
│       ├── app.routes.ts
│       ├── app.config.ts
│       ├── app.component.ts
│       └── windshield-dashboard/             ← NEW DIRECTORY
│           ├── dashboard.component.ts        ← NEW FILE
│           ├── dashboard.component.html      ← NEW FILE
│           ├── dashboard.component.css       ← NEW FILE
│           └── dashboard.service.ts          ← NEW FILE
└── ...other files
```

### Step 2: Update `app.routes.ts` to Add Dashboard Route

Open **`windshield-tester/src/app/app.routes.ts`** and add the dashboard route.

**Import the component** (add to imports section):

```typescript
import { WindshieldDashboardComponent } from './windshield-dashboard/dashboard.component';
```

**Add the route** (add to the routes array):

```typescript
{
  path: 'dashboard',
  component: WindshieldDashboardComponent,
  data: { title: 'Windshield Dashboard' }
}
```

**Example complete app.routes.ts:**

```typescript
import { Routes } from '@angular/router';
import { AppComponent } from './app.component';
import { WindshieldDashboardComponent } from './windshield-dashboard/dashboard.component';

export const routes: Routes = [
  {
    path: '',
    component: AppComponent,
    data: { title: 'Home' }
  },
  {
    path: 'dashboard',
    component: WindshieldDashboardComponent,
    data: { title: 'Windshield Dashboard' }
  },
  {
    path: '**',
    redirectTo: ''
  }
];
```

### Step 3: Verify HttpClientModule is Available

The dashboard service uses `HttpClient`. Make sure your Angular config includes HTTP support.

**Check `app.config.ts` or main.ts:**

```typescript
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';

// In your app config:
export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),  // or HttpClientModule if using NgModules
    // ...other providers
  ]
};
```

If using standalone components (recommended), `provideHttpClient()` should already be available.

### Step 4: Update Service API URL (Optional)

The dashboard service currently uses `http://backend:8000` (Docker) as the base URL.

**For local development**, update `dashboard.service.ts`:

```typescript
// In DashboardService constructor or methods:
// Change from:
private baseUrl = 'http://backend:8000/api/dashboard';

// To:
private baseUrl = 'http://localhost:8000/api/dashboard';
```

**Or use environment configuration** (best practice):

Create `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/dashboard'
};
```

Then in `dashboard.service.ts`:

```typescript
import { environment } from '../../environments/environment';

export class DashboardService {
  private baseUrl = environment.apiUrl;
  // ...
}
```

### Step 5: Build & Run Frontend

```bash
cd windshield-tester

# Install dependencies (if not already done)
npm install

# Start dev server
npm start

# Or with ng CLI:
ng serve --open
```

The app should be available at `http://localhost:4200`

### Step 6: Navigate to Dashboard

Once the Angular dev server is running, visit:

```
http://localhost:4200/dashboard
```

You should see the Windshield Dashboard with:
- Statistics cards
- Filter section
- Test results table
- Pagination controls

---

## ⚙️ CONFIGURATION & ENVIRONMENT

### Backend Environment Variables

Update your `backend/.env` file:

```bash
# Database configuration (should already be set)
DB_URL=mysql+pymysql://root:imad0003@mysql:3306/windshield_db

# Or if using SQLite for testing:
# DB_URL=sqlite:///./test.db
```

### Docker Compose Configuration

Your `docker-compose.yml` should already have:

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DB_URL=mysql+pymysql://root:imad0003@mysql:3306/windshield_db
    depends_on:
      mysql:
        condition: service_healthy

  frontend:
    build: ./windshield-tester
    ports:
      - "4200:4200"
    depends_on:
      - backend
```

### CORS Configuration

The backend already has CORS enabled to accept requests from the frontend:

```python
# In app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For production**, restrict CORS:

```python
allow_origins=[
    "http://frontend:80",
    "http://localhost:4200",
],
```

---

## 🧪 TESTING & VALIDATION

### Test 1: Backend API Health Check

**Using curl:**

```bash
# Check if backend is running
curl http://localhost:8000/docs

# Should return the FastAPI interactive API docs
```

### Test 2: Get All Tests

**Using curl:**

```bash
# Get first 10 tests
curl "http://localhost:8000/api/dashboard/tests?limit=10&offset=0"

# Expected response:
# {
#   "success": true,
#   "data": [
#     {
#       "id": 1,
#       "tension": 110.5,
#       "final_intensity": 45.3,
#       "final_resistance": 2.43,
#       "result": "OK",
#       "created_at": "2026-05-18T14:30:00"
#     }
#   ],
#   "pagination": {
#     "limit": 10,
#     "offset": 0,
#     "total": 150,
#     "pages": 15
#   }
# }
```

### Test 3: Filter by Date Range

```bash
# Get tests between two dates
curl "http://localhost:8000/api/dashboard/tests?start_date=2026-05-01&end_date=2026-05-18"
```

### Test 4: Filter by Result

```bash
# Get only OK tests
curl "http://localhost:8000/api/dashboard/tests?result=OK"

# Get only ERROR tests
curl "http://localhost:8000/api/dashboard/tests?result=ERROR"
```

### Test 5: Export CSV

```bash
# Export all tests
curl "http://localhost:8000/api/dashboard/export" > tests.csv

# Export filtered tests
curl "http://localhost:8000/api/dashboard/export?result=OK&start_date=2026-05-01" > ok_tests.csv

# Check file
head tests.csv
# Should show CSV header: id,tension,final_intensity,final_resistance,result,created_at
```

### Test 6: Get Statistics

```bash
curl "http://localhost:8000/api/dashboard/stats"

# Expected response:
# {
#   "success": true,
#   "data": {
#     "total_tests": 150,
#     "ok_count": 142,
#     "error_count": 8,
#     "ok_percentage": 94.67,
#     "avg_intensity": 44.521,
#     "last_test": "2026-05-18T14:30:00"
#   }
# }
```

### Test 7: Frontend Dashboard Loading

1. Navigate to `http://localhost:4200/dashboard`
2. Should see:
   - **Statistics Cards** at the top (Total Tests, Passed, Failed, Pass Rate, etc.)
   - **Filter Section** with date pickers, status dropdown
   - **Refresh** and **Export CSV** buttons
   - **Data Table** showing test results
   - **Pagination** controls at the bottom

### Test 8: Filter on Frontend

1. Select a date range in the filter
2. Click "Apply Filters"
3. Table should update to show only tests in that date range
4. Pagination should update

### Test 9: Export CSV from Frontend

1. Click "Export CSV" button
2. Browser should download a file named `windshield_tests_YYYYMMDD_HHMMSS.csv`
3. Open CSV in Excel or text editor to verify format

### Test 10: Search by Test ID

1. Enter a test ID in the "Search by Test ID" field
2. Click "Apply Filters"
3. Only that test should appear (if it exists)

### Test 11: Pagination

1. Change "Rows per page" to 5
2. Click page navigation buttons
3. Table should update to show different pages

### Test 12: Error Handling

1. Try invalid date format: enter "invalid-date" in date field
2. Should see error: "Invalid start_date format. Use YYYY-MM-DD"
3. Try searching for non-existent test ID (e.g., 999999)
4. Should see: "No test records found matching your filters"

---

## 🐛 TROUBLESHOOTING

### Problem: "Cannot GET /api/dashboard/tests"

**Solution:**
- Verify router is mounted in `app.py`
- Check backend logs: `docker-compose logs backend`
- Make sure backend container is running: `docker-compose ps`

### Problem: "Connection refused" from frontend

**Solution:**
- Backend may not be running
- Check CORS configuration
- Verify API URL in `dashboard.service.ts` matches backend URL
- For Docker: use `http://backend:8000`, for local dev: use `http://localhost:8000`

### Problem: "No data showing in table"

**Solution:**
- Check if database has test data
- Run: `curl http://localhost:8000/api/dashboard/tests`
- If empty, run tests in backend to populate database
- Check MySQL directly:
  ```bash
  docker exec windshield-mysql mysql -u root -p"imad0003" -D windshield_db -e "SELECT COUNT(*) FROM windshield_test;"
  ```

### Problem: "CORS error in browser console"

**Solution:**
- Check `app.py` has CORS middleware configured
- Allow frontend origin in `allow_origins` list
- For development, `allow_origins=["*"]` is fine
- Reload frontend in browser

### Problem: "Export CSV returns empty file"

**Solution:**
- Verify database has data
- Check if filters are too restrictive
- Test with no filters: `/api/dashboard/export`

### Problem: Angular component not loading

**Solution:**
- Verify file path: `src/app/windshield-dashboard/dashboard.component.ts`
- Check route in `app.routes.ts` points to correct component
- Verify imports are correct
- Check browser console for errors (F12)

### Problem: "Cannot find module '@angular/common/http'"

**Solution:**
- Ensure `HttpClientModule` or `provideHttpClient()` is in your app config
- Install dependencies: `npm install`
- Check `angular.json` and main configuration files

### Problem: Date filters not working

**Solution:**
- Use format YYYY-MM-DD (e.g., 2026-05-18)
- Check both start_date AND end_date fields
- Backend expects ISO format: YYYY-MM-DD HH:MM:SS

---

## ✅ VERIFICATION CHECKLIST

Use this checklist to verify everything is integrated correctly:

- [ ] Dashboard router file exists: `backend/dashboard_router.py`
- [ ] Router imported in `backend/app.py`
- [ ] Router mounted in `backend/app.py`
- [ ] Backend running without errors
- [ ] Dashboard component files exist in `windshield-tester/src/app/windshield-dashboard/`
- [ ] Dashboard component imported in `app.routes.ts`
- [ ] Dashboard route added to routes array
- [ ] Frontend running without errors
- [ ] Can navigate to `http://localhost:4200/dashboard`
- [ ] Statistics cards display with numbers
- [ ] Test table displays data
- [ ] Filters work (date range, result)
- [ ] Export CSV downloads a file
- [ ] Pagination works
- [ ] Error messages display appropriately
- [ ] No CORS errors in browser console
- [ ] No 404 errors for API requests

---

## 📞 SUPPORT

If you encounter issues:

1. **Check logs:**
   ```bash
   docker-compose logs backend     # Backend logs
   docker-compose logs frontend    # Frontend logs
   ```

2. **Verify connectivity:**
   ```bash
   curl http://localhost:8000/api/dashboard/tests
   curl http://localhost:4200/dashboard
   ```

3. **Restart containers:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

4. **Check database:**
   ```bash
   docker exec windshield-mysql mysql -u root -p"imad0003" windshield_db
   ```

---

## 📚 API REFERENCE

### GET /api/dashboard/tests

**Parameters:**
- `limit` (int, default 10): Number of results per page
- `offset` (int, default 0): Number of results to skip
- `result` (string, optional): 'OK' or 'ERROR'
- `start_date` (string, optional): YYYY-MM-DD
- `end_date` (string, optional): YYYY-MM-DD

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "tension": 110.5,
      "final_intensity": 45.3,
      "final_resistance": 2.43,
      "result": "OK",
      "created_at": "2026-05-18T14:30:00"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 150,
    "pages": 15
  }
}
```

### GET /api/dashboard/tests/{id}

**Parameters:**
- `id` (int): Test ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "tension": 110.5,
    "final_intensity": 45.3,
    "final_resistance": 2.43,
    "result": "OK",
    "created_at": "2026-05-18T14:30:00"
  }
}
```

### GET /api/dashboard/export

**Parameters:**
- `result` (string, optional): 'OK' or 'ERROR'
- `start_date` (string, optional): YYYY-MM-DD
- `end_date` (string, optional): YYYY-MM-DD

**Response:** CSV file content

### GET /api/dashboard/stats

**Response:**
```json
{
  "success": true,
  "data": {
    "total_tests": 150,
    "ok_count": 142,
    "error_count": 8,
    "ok_percentage": 94.67,
    "avg_intensity": 44.521,
    "last_test": "2026-05-18T14:30:00"
  }
}
```

---

## 🎉 SUCCESS!

Once all integration steps are complete and tests pass, your Windshield Dashboard will be:

✅ **Live and accessible** at `http://localhost:4200/dashboard`  
✅ **Fully functional** with filters, pagination, and exports  
✅ **Read-only and secure** (no delete/edit operations)  
✅ **Simple for managers** (no technical jargon or complexity)  
✅ **Connected to MySQL** database with real-time data  

**Dashboard Features:**
- 📊 Real-time statistics cards
- 🔍 Advanced filtering (date range, status)
- 📄 One-click CSV export
- 📑 Pagination with customizable page size
- 🎨 Clean, manager-friendly UI with large fonts
- ⚡ Fast loading with error handling
- 📱 Responsive design for tablets and phones

Enjoy your new Windshield Dashboard! 🚀
