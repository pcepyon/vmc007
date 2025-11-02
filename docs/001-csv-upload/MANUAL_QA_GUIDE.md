# CSV Upload Feature - Manual QA Guide

**Feature:** CSV/Excel File Upload and Data Parsing
**Version:** 1.0
**Date:** 2025-11-02
**Testing Environment:** Local Development

---

## Prerequisites

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd /Users/pro16/Desktop/project/VMC007/backend
```

2. **Activate virtual environment:**
```bash
source venv/bin/activate
```

3. **Create .env file if not exists:**
```bash
cat > .env <<EOF
DEBUG=True
ADMIN_API_KEY=your-admin-key-12345
DATABASE_URL=your_supabase_connection_string
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Start backend server:**
```bash
python manage.py runserver
```

Expected output:
```
Django version X.X.X, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
```

### Frontend Setup

1. **Navigate to frontend directory (new terminal):**
```bash
cd /Users/pro16/Desktop/project/VMC007/frontend
```

2. **Verify .env.local exists:**
```bash
cat .env.local
```

Expected content:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_ADMIN_MODE=true
VITE_ADMIN_API_KEY=your-admin-key-12345
```

3. **Install dependencies (if not done):**
```bash
npm install
```

4. **Start frontend dev server:**
```bash
npm run dev
```

Expected output:
```
VITE vX.X.X ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## Test Scenarios

### Scenario 1: Successful 4-File Upload (Happy Path) ✅

**Objective:** Verify complete upload flow with all 4 file types

**Test Data Required:**
- `research_project_data.csv` (10-50 rows)
- `student_roster.csv` (10-50 rows)
- `publication_list.csv` (10-50 rows)
- `department_kpi.csv` (5-20 rows)

**Steps:**

1. **Open browser and navigate to upload page:**
   - URL: `http://localhost:5173/admin/upload`
   - Expected: Upload UI with 4 file selection areas

2. **Select files:**
   - Click "Research Funding" file input → select `research_project_data.csv`
   - Click "Students" file input → select `student_roster.csv`
   - Click "Publications" file input → select `publication_list.csv`
   - Click "Department KPI" file input → select `department_kpi.csv`

   Expected after each selection:
   - File name displayed
   - File size shown (e.g., "2.3 KB")
   - "Ready" status icon

3. **Initiate upload:**
   - Click "Upload Files" button
   - Expected immediate response:
     - Button disabled
     - Loading indicator appears
     - Status message: "Processing files..."

4. **Monitor upload status:**
   - Observe progress indicators updating every 3 seconds
   - Expected intermediate states:
     - "Processing: research_funding (25%)"
     - "Processing: students (50%)"
     - "Processing: publications (75%)"
     - "Completed: 4/4 files (100%)"

5. **Verify completion:**
   - Expected final UI state:
     - ✅ Green success banner
     - Message: "Upload completed successfully!"
     - Statistics displayed:
       - "Total files: 4/4 success"
       - "Total rows inserted: XXX"
       - "Processing time: X.X seconds"
     - Action buttons:
       - "View Dashboard" (navigates to `/dashboard`)
       - "Upload More" (resets form)

6. **Verify backend data:**
```bash
# In backend terminal
python manage.py shell
>>> from data_ingestion.infrastructure.models import ResearchProject, StudentRoster, Publication, DepartmentKPI
>>> ResearchProject.objects.count()
XXX  # Should match uploaded row count
>>> StudentRoster.objects.count()
XXX
>>> Publication.objects.count()
XXX
>>> DepartmentKPI.objects.count()
XXX
```

**Pass Criteria:**
- ✅ All 4 files uploaded without errors
- ✅ Status polling stopped after completion
- ✅ Database contains correct row counts
- ✅ No console errors in browser DevTools
- ✅ Backend logs show no errors

---

### Scenario 2: Authentication Failure (403 Forbidden) ⚠️

**Objective:** Verify API key validation

**Steps:**

1. **Modify frontend .env.local:**
```bash
VITE_ADMIN_API_KEY=wrong-api-key
```

2. **Restart frontend dev server:**
```bash
# Ctrl+C then
npm run dev
```

3. **Navigate to upload page:**
   - URL: `http://localhost:5173/admin/upload`

4. **Select and upload any file:**
   - Choose 1 CSV file
   - Click "Upload Files"

**Expected Result:**
- ❌ Error banner appears
- Message: "관리자 권한이 없습니다. 접근이 거부되었습니다."
- HTTP Status: 403 Forbidden (visible in Network tab)
- Upload form remains interactive
- "Retry" button available

**Pass Criteria:**
- ✅ 403 error correctly displayed
- ✅ No data uploaded to database
- ✅ User-friendly error message
- ✅ Form remains usable for retry

**Cleanup:** Restore correct API key in `.env.local` and restart frontend

---

### Scenario 3: File Size Validation (>10MB) ⚠️

**Objective:** Verify client and server-side file size validation

**Test Data:**
- Create large file: `dd if=/dev/zero of=large_file.csv bs=1048576 count=11` (11MB file)

**Steps:**

1. **Navigate to upload page**

2. **Select large file:**
   - Choose the 11MB CSV file

**Expected Result (Client-side validation):**
- ⚠️ Warning message appears immediately
- Message: "File size exceeds 10MB limit (current: 11.0 MB)"
- File not accepted
- "Upload Files" button remains disabled

**Alternative Test (if client validation bypassed):**
- Modify client code temporarily to skip validation
- Upload 11MB file
- Expected server response:
  - HTTP 400 Bad Request
  - Error: "FILE_TOO_LARGE"

**Pass Criteria:**
- ✅ File rejected before upload starts
- ✅ Clear error message with actual file size
- ✅ No unnecessary network requests

---

### Scenario 4: Missing Required Column 📋

**Objective:** Verify data validation during parsing

**Test Data:**
- Create `invalid_research.csv` without "집행ID" column:
```csv
소속학과,총연구비,집행일자,집행금액
컴퓨터공학과,10000000,2025-01-15,5000000
```

**Steps:**

1. **Navigate to upload page**

2. **Upload invalid file:**
   - Select `invalid_research.csv` for Research Funding
   - Click "Upload Files"

3. **Wait for processing:**
   - Status will change to "processing" → "failed"

**Expected Result:**
- ❌ Error state for research_funding file
- Detailed error message:
  - "Required column '집행ID' is missing"
  - "Expected columns: [집행ID, 소속학과, 총연구비, 집행일자, 집행금액]"
- Other files (if uploaded) process normally
- Partial success UI if other files succeeded

**Pass Criteria:**
- ✅ Validation error clearly explains issue
- ✅ Lists expected columns
- ✅ Parsing stops for invalid file
- ✅ No invalid data inserted into database

---

### Scenario 5: Partial Success (3 Success, 1 Failure) ✅ ⚠️

**Objective:** Verify independent file processing and partial success handling

**Test Data:**
- 3 valid CSV files (research, students, publications)
- 1 invalid CSV file (kpi without required column)

**Steps:**

1. **Navigate to upload page**

2. **Select 4 files:**
   - 3 valid files
   - 1 intentionally invalid KPI file

3. **Upload and monitor:**
   - Click "Upload Files"
   - Observe status changes

**Expected Result:**
- ⚠️ Orange warning banner (not green, not red)
- Message: "Upload partially completed"
- File status breakdown:
   - ✅ research_funding: Completed (XXX rows)
   - ✅ students: Completed (XXX rows)
   - ✅ publications: Completed (XXX rows)
   - ❌ kpi: Failed - "Required column missing"
- Action buttons:
   - "Upload Failed Files Only" (opens dialog to select only KPI file)
   - "Upload All Again" (resets form)

**Pass Criteria:**
- ✅ Successful files data persisted in database
- ✅ Failed file data NOT in database
- ✅ Clear indication of which file failed and why
- ✅ Option to retry only failed file

---

### Scenario 6: Network Disconnection and Recovery 🌐

**Objective:** Verify error handling during network issues

**Steps:**

1. **Navigate to upload page**

2. **Select files and initiate upload:**
   - Choose any valid CSV file
   - Click "Upload Files"

3. **Simulate network failure:**
   - Open Chrome DevTools → Network tab
   - Enable "Offline" mode AFTER upload starts but BEFORE first status poll

4. **Observe error handling:**
   - Status polling will fail after 3 seconds

**Expected Result:**
- ⚠️ Warning message: "Network connection lost. Retrying..."
- Status polling pauses
- Automatic retry after reconnection (if implemented) OR manual retry button

5. **Re-enable network:**
   - Disable "Offline" mode in DevTools

6. **Verify recovery:**
   - If auto-retry: Status polling resumes automatically
   - If manual: "Retry" button re-initiates polling
   - Eventually shows completion status (backend processing continued)

**Pass Criteria:**
- ✅ Network error detected and displayed
- ✅ User informed of connection issue
- ✅ Processing continues on backend
- ✅ Status recoverable after reconnection

---

## Testing Checklist

### Pre-Test Setup
- [ ] Backend server running (port 8000)
- [ ] Frontend dev server running (port 5173)
- [ ] Database migrated and accessible
- [ ] .env files correctly configured
- [ ] Test CSV files prepared
- [ ] Browser DevTools open (Network + Console tabs)

### Test Execution
- [ ] Scenario 1: Happy Path ✅
- [ ] Scenario 2: Auth Failure ⚠️
- [ ] Scenario 3: File Size Validation ⚠️
- [ ] Scenario 4: Missing Column 📋
- [ ] Scenario 5: Partial Success ✅⚠️
- [ ] Scenario 6: Network Recovery 🌐

### Post-Test Verification
- [ ] No console errors in browser
- [ ] Backend logs reviewed (no unexpected errors)
- [ ] Database state verified (correct row counts)
- [ ] All test data cleaned up
- [ ] Environment variables restored

---

## Expected File Formats

### research_project_data.csv
```csv
집행ID,소속학과,총연구비,집행일자,집행금액
PROJ001,컴퓨터공학과,10000000,2025-01-15,5000000
PROJ002,전자공학과,8000000,2025-01-16,3000000
```

### student_roster.csv
```csv
학번,학과,학년,과정구분,학적상태
2024001,컴퓨터공학과,1,학사,재학
2024002,전자공학과,2,학사,재학
2023001,컴퓨터공학과,1,석사,재학
```

### publication_list.csv
```csv
논문ID,학과,저널등급,Impact Factor
PUB001,컴퓨터공학과,SCIE,3.5
PUB002,전자공학과,KCI,
PUB003,기계공학과,SCIE,5.2
```

### department_kpi.csv
```csv
평가년도,학과,졸업생 취업률(%),연간 기술이전 수입액(억원)
2024,컴퓨터공학과,85.5,12.3
2024,전자공학과,82.0,8.7
2023,컴퓨터공학과,83.2,10.5
```

---

## Troubleshooting

### Issue: "Cannot connect to backend"
**Solution:**
1. Verify backend server is running: `ps aux | grep "python manage.py runserver"`
2. Check VITE_API_BASE_URL in frontend/.env.local
3. Ensure CORS is configured in backend settings

### Issue: "API key validation failing"
**Solution:**
1. Compare keys in backend/.env and frontend/.env.local
2. Restart both servers after changing env files
3. Check Django logs for actual key being sent

### Issue: "Files uploading but data not in database"
**Solution:**
1. Check Django console for parsing errors
2. Verify database connection: `python manage.py dbshell`
3. Review CSV file encoding (should be UTF-8)

### Issue: "Status polling never completes"
**Solution:**
1. Check backend console for job processing errors
2. Verify job_id in Network tab matches backend logs
3. Check if background thread is running (backend logs)

---

## Test Result Template

```markdown
## QA Test Results - CSV Upload Feature

**Tester:** [Your Name]
**Date:** [YYYY-MM-DD]
**Environment:** Local Development
**Backend Version:** [git commit hash]
**Frontend Version:** [git commit hash]

### Test Summary
- Total Scenarios: 6
- Passed: X
- Failed: X
- Blocked: X

### Scenario Results

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. Happy Path | ✅ PASS | All 4 files uploaded successfully |
| 2. Auth Failure | ✅ PASS | 403 error displayed correctly |
| 3. File Size | ✅ PASS | Validation works on client |
| 4. Missing Column | ✅ PASS | Error message clear |
| 5. Partial Success | ✅ PASS | UI shows 3/4 success |
| 6. Network Recovery | ❌ FAIL | Auto-retry not working |

### Issues Found
1. **[Bug #001]** Network auto-retry not implemented
   - Severity: Medium
   - Reproduction: Scenario 6, step 4
   - Expected: Auto-retry after reconnection
   - Actual: Manual retry button required

### Recommendations
- Implement automatic status polling retry on network recovery
- Add loading skeleton for better UX during polling
- Consider adding file preview before upload

**Overall Assessment:** Feature ready for internal beta testing with minor UX improvements needed.
```

---

## Success Criteria

### MVP Acceptance Criteria
- ✅ All 6 scenarios pass (or have acceptable workarounds)
- ✅ No critical bugs (data loss, security issues)
- ✅ Error messages are user-friendly in Korean
- ✅ Performance: 10MB file uploads in <2 minutes
- ✅ Browser compatibility: Chrome, Safari latest versions

### Production Readiness (Post-MVP)
- Integration with authentication system
- Automated E2E tests passing
- Error logging to monitoring system
- File upload progress percentage
- Comprehensive error recovery

---

**End of Manual QA Guide**
