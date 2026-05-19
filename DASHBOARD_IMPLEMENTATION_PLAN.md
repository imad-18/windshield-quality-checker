# Windshield Dashboard - Implementation Plan
## Read-Only Production Manager Dashboard

---

## OVERVIEW

A simple, clean dashboard for production managers to view windshield test results from MySQL without technical knowledge. No login required, no database access, just clean data visualization.

**Project Goals:**
- ✅ Read-only access to test results
- ✅ Simple, non-technical UI
- ✅ Real-time data from MySQL
- ✅ Export capabilities (CSV)
- ✅ Filtering and pagination
- ✅ No admin/edit functions

---

## PHASE 1: FASTAPI BACKEND IMPLEMENTATION

### 1.1 New File: `backend/dashboard_router.py`

**Purpose**: Dedicated router for all read-only dashboard endpoints

**Endpoints to implement**:
- `GET /api/dashboard/tests` - List all tests with pagination/filters
- `GET /api/dashboard/tests/{id}` - Get single test by ID
- `GET /api/dashboard/export` - Export filtered tests as CSV
- `GET /api/dashboard/stats` - Summary statistics

**Features**:
- Pagination (limit, offset)
- Filters: date_range, result, operator
- Search by ID
- Error handling
- CSV generation

### 1.2 Update: `backend/app.py`

**Changes needed**:
- Import and include dashboard_router
- Mount router at `/api/dashboard`

### 1.3 Database Queries

**Use existing models**:
- `WindshieldTest` from models.py
- `Session` from database.py

---

## PHASE 2: ANGULAR FRONTEND IMPLEMENTATION

### 2.1 New Component: `windshield-dashboard`

**File structure**:
```
windshield-tester/src/app/windshield-dashboard/
├── dashboard.component.ts
├── dashboard.component.html
├── dashboard.component.css
├── dashboard.service.ts
```

**Features**:
- Dashboard table component
- Filter panel (date, result, search)
- Pagination controls
- Export button
- Refresh button
- Loading/error states

### 2.2 Service: `dashboard.service.ts`

**Methods**:
- `getTests(filters)` - Fetch filtered test data
- `getTestById(id)` - Get single test
- `exportCSV(filters)` - Download CSV
- `getStats()` - Get summary stats

### 2.3 Routing Integration

**Update**: `app/app.routes.ts`
- Add route to dashboard component
- Make it accessible from main navigation

---

## PHASE 3: USER EXPERIENCE

### Design Principles

1. **Simplicity**: Large fonts, minimal colors, clear layout
2. **No Tech Jargon**: Use "Test Status" not "Result", "Test Date" not "created_at"
3. **Quick Access**: Filters visible, export one-click
4. **Error Handling**: User-friendly messages, no stack traces
5. **Mobile-Friendly**: Works on tablets/laptops

### Layout

```
┌─ WINDSHIELD TEST DASHBOARD ───────────────────────┐
│                                                    │
│ [Refresh]                              [Export CSV]│
│                                                    │
│ Filters:                                           │
│  From: [Date] To: [Date]  Status: [OK/NOK/All]   │
│  [Search by Test ID...]                [APPLY]   │
│                                                    │
├────────────────────────────────────────────────────┤
│ ID │ Tension │ Intensity │ Resistance │ Status │Time│
├────────────────────────────────────────────────────┤
│ 1  │ 20.0    │ 1.048     │ 19.08      │ OK     │... │
│ 2  │ 20.0    │ 0.92      │ 21.74      │ ERROR  │... │
│ 3  │ 20.0    │ 1.12      │ 17.86      │ OK     │... │
├────────────────────────────────────────────────────┤
│ Page 1 of 5 | [< Previous] [Next >] | Rows: 10   │
└────────────────────────────────────────────────────┘
```

---

## PHASE 4: DATA FLOW

```
┌─────────────────────┐
│  Production Manager │
└──────────┬──────────┘
           │
           │ Opens Dashboard
           ↓
┌──────────────────────────────────┐
│  Angular Dashboard Component     │
│  • Displays filters              │
│  • Shows test table              │
│  • Pagination controls           │
└──────────┬───────────────────────┘
           │ API Calls via HttpClient
           ↓
┌──────────────────────────────────┐
│  FastAPI Router (/api/dashboard) │
│  • Handles GET requests          │
│  • Filters & paginates data      │
│  • Generates CSV                 │
└──────────┬───────────────────────┘
           │ SQLAlchemy Queries
           ↓
┌──────────────────────────────────┐
│  MySQL Database                  │
│  • windshield_tests table        │
│  • Returns filtered results      │
└──────────────────────────────────┘
```

---

## PHASE 5: API RESPONSE EXAMPLES

### Example 1: GET /api/dashboard/tests

**Request**:
```
GET /api/dashboard/tests?limit=10&offset=0&result=OK&start_date=2026-05-01&end_date=2026-05-18
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "tension": 20.0,
      "final_intensity": 1.048,
      "final_resistance": 19.08,
      "result": "OK",
      "created_at": "2026-05-18T10:50:32"
    },
    {
      "id": 3,
      "tension": 20.0,
      "final_intensity": 1.12,
      "final_resistance": 17.86,
      "result": "OK",
      "created_at": "2026-05-18T10:52:03"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 2,
    "pages": 1
  }
}
```

### Example 2: GET /api/dashboard/tests/1

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "tension": 20.0,
    "final_intensity": 1.048,
    "final_resistance": 19.08,
    "result": "OK",
    "created_at": "2026-05-18T10:50:32"
  }
}
```

### Example 3: GET /api/dashboard/export?result=OK

**Response** (200 OK - text/csv):
```
id,tension,final_intensity,final_resistance,result,created_at
1,20.0,1.048,19.08,OK,2026-05-18 10:50:32
3,20.0,1.12,17.86,OK,2026-05-18 10:52:03
```

### Example 4: GET /api/dashboard/stats

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "total_tests": 5,
    "ok_count": 3,
    "error_count": 2,
    "ok_percentage": 60.0,
    "avg_intensity": 1.032,
    "last_test": "2026-05-18T11:02:45"
  }
}
```

---

## PHASE 6: TESTING CHECKLIST

### Backend Tests

- [ ] GET /api/dashboard/tests returns all tests
- [ ] Pagination works (limit, offset)
- [ ] Filters work (date range, result)
- [ ] Search by ID works
- [ ] CSV export generates valid CSV
- [ ] Error handling returns 500 for DB errors
- [ ] Stats endpoint returns correct calculations

### Frontend Tests

- [ ] Dashboard loads without errors
- [ ] Table displays all columns correctly
- [ ] Filters apply correctly
- [ ] Pagination buttons work
- [ ] CSV export downloads file
- [ ] Loading spinner shows during requests
- [ ] Error messages display on API failure
- [ ] "No results" message shows when empty
- [ ] Refresh button reloads data
- [ ] Responsive design on mobile/tablet

### Integration Tests

- [ ] Backend connects to MySQL correctly
- [ ] Frontend connects to backend API
- [ ] Data flows from DB → API → Frontend
- [ ] Real test data appears in dashboard
- [ ] Exported CSV can be opened in Excel
- [ ] Filters work end-to-end
- [ ] No console errors in browser

---

## PHASE 7: DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] Environment variables set correctly (DATABASE_URL, BACKEND_API_URL)
- [ ] Docker Compose builds without errors
- [ ] All containers start successfully
- [ ] Dashboard accessible at http://localhost:4200/dashboard
- [ ] phpMyAdmin shows correct data
- [ ] Test data visible in both dashboard and phpMyAdmin
- [ ] CSV export opens correctly
- [ ] Performance acceptable with large datasets

---

## DELIVERABLES CHECKLIST

### Backend
- [ ] dashboard_router.py (complete with all endpoints)
- [ ] Integration into app.py
- [ ] Pydantic schemas for responses
- [ ] Error handling and logging

### Frontend
- [ ] dashboard.component.ts (logic and filters)
- [ ] dashboard.component.html (template)
- [ ] dashboard.component.css (styling)
- [ ] dashboard.service.ts (API calls)
- [ ] Routing configuration updates
- [ ] Module imports (DatePipe, FormsModule, etc.)

### Documentation
- [ ] API endpoint documentation
- [ ] Component usage guide
- [ ] Filter parameters guide
- [ ] CSV export format guide
- [ ] Troubleshooting guide

---

## FILE CREATION SUMMARY

**New Backend Files**:
1. `backend/dashboard_router.py` - Main router (NEW)

**Updated Backend Files**:
1. `backend/app.py` - Add router import and mount

**New Frontend Files**:
1. `windshield-tester/src/app/windshield-dashboard/dashboard.component.ts` - Component logic
2. `windshield-tester/src/app/windshield-dashboard/dashboard.component.html` - Template
3. `windshield-tester/src/app/windshield-dashboard/dashboard.component.css` - Styles
4. `windshield-tester/src/app/windshield-dashboard/dashboard.service.ts` - API service

**Updated Frontend Files**:
1. `windshield-tester/src/app/app.routes.ts` - Add dashboard route
2. `windshield-tester/src/app/app.component.html` - Add dashboard link (optional)

---

## NEXT STEPS

1. Review this implementation plan
2. Review the code in the following sections
3. Create backend files
4. Create frontend files
5. Update integrations (app.py, app.routes.ts)
6. Test each endpoint with curl/Postman
7. Test Angular components in browser
8. Run end-to-end tests
9. Deploy and verify

