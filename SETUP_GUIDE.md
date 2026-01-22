# Faculty-Facing Attendance Portal - Setup & Run Guide

## Prerequisites

- Python 3.8+ with pip
- Node.js 18+ with npm
- Webcam for face recognition
- Face data and encodings.pkl (from training)

---

## Backend Setup

### 1. Install Python Dependencies

```bash
cd C:\Users\shemi\Documents\Face
pip install -r requirements.txt
```

### 2. Initialize Database

Run the seeding script to create tables and populate initial data:

```bash
python backend\seed_data.py
```

This will:
- Create all database tables in `attendance.db`
- Import students from `data/students.csv`
- Create AIML-A class with password `faculty@123`
- Populate timetable for AIML-A

### 3. Start Backend Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**

API docs: **http://localhost:8000/docs**

---

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd C:\Users\shemi\Documents\Face\frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## Usage

### Login

1. Open http://localhost:5173
2. Enter credentials:
   - **Username**: AIML-A
   - **Password**: faculty@123
3. Click Login

### Mark Attendance

1. View today's timetable on the dashboard
2. Click **"Start Attendance"** for a period
3. Camera will open and start recognizing faces automatically
4. Manually override attendance if needed using the dropdowns
5. Click **"End Session"** when done

### View Reports

1. Select a date in the "Previous Attendance Reports" section
2. Click **"Load Sessions"**
3. Click **"View"** to see the report or **"Download Excel"** to export

---

## Adding New Students

### 1. Capture Face Data

```bash
python src\capture_faces.py
```

Enter student name (this will be used for recognition)

### 2. Train Model

```bash
python src\train_model.py
```

This updates `models/encodings.pkl`

### 3. Add Student to Database

```bash
python src\setup_students.py
```

Map the student name to Reg No, Class, and Email

### 4. Reload Encodings (Optional)

If backend is running, you can reload encodings without restart:

```bash
curl -X POST http://localhost:8000/api/reload-encodings -H "Authorization: Bearer YOUR_TOKEN"
```

Or just restart the backend server.

---

## Project Structure

```
Face/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database config
│   ├── auth.py              # Authentication
│   ├── face_recognition_service.py  # Face recognition
│   └── seed_data.py         # Database seeding
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AttendanceSession.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── utils/
│   │   │   ├── api.js
│   │   │   └── auth.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── known_faces/         # Student face images
│   └── students.csv         # Student database
├── models/
│   └── encodings.pkl        # Face encodings
├── attendance.db            # SQLite database (created on first run)
└── requirements.txt
```

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - Faculty login

### Timetable
- `GET /api/timetable/today` - Get today's timetable

### Attendance
- `POST /api/attendance/start-session` - Start attendance session
- `GET /api/attendance/session/{id}` - Get session details
- `POST /api/attendance/end-session/{id}` - End session
- `GET /api/attendance/session/{id}/students` - Get student list
- `POST /api/attendance/manual-override` - Manual attendance change

### Reports
- `GET /api/reports/sessions?date={date}` - Get sessions by date
- `GET /api/reports/session/{id}/report` - Get session report
- `GET /api/reports/session/{id}/export` - Download Excel

### Utility
- `POST /api/reload-encodings` - Reload face encodings
- `GET /api/health` - Health check

---

## Troubleshooting

### Camera Not Working
- Grant browser camera permissions
- Check if another application is using the camera
- Try a different browser (Chrome recommended)

### Face Not Recognized
- Ensure face encodings are trained (`train_model.py`)
- Check if student name in `data/students.csv` matches folder name in `data/known_faces/`
- Verify face is well-lit and clearly visible

### Backend Errors
- Check if port 8000 is available
- Verify all dependencies are installed
- Check `attendance.db` exists and is not corrupted

### Frontend Build Errors
- Delete `node_modules` and run `npm install` again
- Clear browser cache
- Check console for JavaScript errors

---

## Production Deployment

### Backend

1. Set environment variable for SECRET_KEY in `backend/auth.py`
2. Use PostgreSQL instead of SQLite (update `database.py`)
3. Run with Gunicorn:
   ```bash
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Frontend

1. Build production bundle:
   ```bash
   npm run build
   ```
2. Serve the `dist/` folder with Nginx or Apache
3. Update API base URL in `src/utils/api.js`

---

## License & Credits

Built with:
- FastAPI
- React
- Tailwind CSS  
- FaceNet
- SQLAlchemy
- OpenCV
