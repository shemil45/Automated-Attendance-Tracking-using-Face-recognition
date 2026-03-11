# 🎓 AttendNet — Automated Attendance Tracking using Face Recognition

A faculty-facing web portal that automates student attendance using real-time face recognition powered by **FaceNet** and **OpenCV**. Faculty can start an attendance session for any class period, and the system automatically recognizes students via webcam.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, SQLAlchemy, Python 3.11 |
| **Frontend** | React 19, Vite, Tailwind CSS |
| **Face Recognition** | FaceNet (keras-facenet), OpenCV DNN |
| **Database** | Supabase (PostgreSQL) / SQLite (local) |
| **Auth** | JWT (python-jose) |

---

## 📋 Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.11.9** — [Download](https://www.python.org/downloads/release/python-3119/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **Git** — [Download](https://git-scm.com/)
- A **webcam** for face recognition

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/shemil45/Automated-Attendance-Tracking-using-Face-recognition.git
cd Automated-Attendance-Tracking-using-Face-recognition
```

---

### 2. Backend Setup

#### a. Create & Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

#### b. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ TensorFlow may take a few minutes to install.

#### c. Configure Environment Variables

Create a `.env` file in the project root (copy from the example below):

```env
# Database — choose one:

# Option A: Supabase (PostgreSQL) — recommended for production
USE_SUPABASE=true
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/postgres

# Option B: Local SQLite — for offline/local development
USE_SUPABASE=false

# JWT Secret (change this in production!)
SECRET_KEY=your_secret_key_here

# Supabase API Keys (optional, for future features)
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_KEY=<your-service-key>
```

#### d. Seed the Database

Run the seeding script to create tables and populate initial data:

```bash
python backend/seed_data.py
```

This will:
- Create all database tables
- Import students from `data/students.csv`
- Create the **AIML-A** class with default credentials
- Populate the timetable

#### e. Start the Backend Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base URL: **http://localhost:8000**
- Interactive API Docs: **http://localhost:8000/docs**

---

### 3. Frontend Setup

#### a. Install Node Dependencies

```bash
cd frontend
npm install
```

#### b. Start the Development Server

```bash
npm run dev
```

- Frontend URL: **http://localhost:5173**

---

## 🔑 Default Login Credentials

| Field | Value |
|---|---|
| **Username** | `AIML-A` |
| **Password** | `faculty@123` |

---

## 📖 Usage

### Mark Attendance
1. Open **http://localhost:5173** and log in
2. View today's timetable on the dashboard
3. Click **"Start Attendance"** for a period
4. The camera opens and begins recognizing faces automatically
5. Manually override attendance using the dropdowns if needed
6. Click **"End Session"** when done

### View Reports
1. Select a date in the **"Previous Attendance Reports"** section
2. Click **"Load Sessions"**
3. Click **"View"** to see the report or **"Download Excel"** to export

---

## 👤 Adding New Students

### Step 1 — Capture Face Data
```bash
python src/capture_faces.py
```
Enter the student's name when prompted. Face images are saved to `data/known_faces/`.

### Step 2 — Train the Model
```bash
python src/train_model.py
```
This updates `models/encodings.pkl` with the new student's face encodings.

### Step 3 — Add Student to Database
```bash
python src/setup_students.py
```
Map the student name to their Registration Number, Class, and Email.

### Step 4 — Reload Encodings (Optional)
If the backend is already running, reload without restarting:
```bash
curl -X POST http://localhost:8000/api/reload-encodings \
  -H "Authorization: Bearer YOUR_TOKEN"
```
Or simply restart the backend server.

---

## 📁 Project Structure

```
Face/
├── backend/
│   ├── main.py                    # FastAPI app & all API routes
│   ├── models.py                  # SQLAlchemy database models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── database.py                # Database connection config
│   ├── auth.py                    # JWT authentication
│   ├── face_recognition_service.py # FaceNet face recognition logic
│   └── seed_data.py               # Database seeding script
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Login.jsx
│       │   ├── Dashboard.jsx
│       │   ├── AttendanceSession.jsx
│       │   └── ProtectedRoute.jsx
│       └── utils/
│           ├── api.js
│           └── auth.js
├── data/
│   ├── known_faces/               # Student face images (per student folder)
│   └── students.csv               # Student roster
├── models/
│   └── encodings.pkl              # Trained face encodings
├── src/
│   ├── capture_faces.py           # Capture face images for a student
│   ├── train_model.py             # Train FaceNet encodings
│   └── setup_students.py         # Add students to the database
├── .env                           # Environment variables (not committed)
├── requirements.txt               # Python dependencies
├── Procfile                       # Deployment config (Render/Heroku)
└── attendance.db                  # SQLite DB (created on first run, local only)
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Faculty login |
| `GET` | `/api/timetable/today` | Get today's timetable |
| `POST` | `/api/attendance/start-session` | Start attendance session |
| `GET` | `/api/attendance/session/{id}` | Get session details |
| `POST` | `/api/attendance/end-session/{id}` | End session |
| `GET` | `/api/attendance/session/{id}/students` | Get student list |
| `POST` | `/api/attendance/manual-override` | Manual attendance change |
| `GET` | `/api/reports/sessions?date={date}` | Get sessions by date |
| `GET` | `/api/reports/session/{id}/report` | Get session report |
| `GET` | `/api/reports/session/{id}/export` | Download Excel report |
| `POST` | `/api/reload-encodings` | Reload face encodings |
| `GET` | `/api/health` | Health check |

---

## 🚢 Production Deployment

### Backend (Render / Heroku)

The `Procfile` is already configured:
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Set the following environment variables on your hosting platform:
- `DATABASE_URL` — your PostgreSQL connection string
- `SECRET_KEY` — a strong random secret
- `USE_SUPABASE=true`

### Frontend

```bash
cd frontend
npm run build
```
Serve the generated `dist/` folder via Nginx, Apache, or a static hosting service (Vercel, Netlify, etc.). Update the API base URL in `src/utils/api.js` to point to your deployed backend.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **Camera not working** | Grant browser camera permissions; try Chrome |
| **Face not recognized** | Re-run `train_model.py`; ensure good lighting |
| **Backend won't start** | Check port 8000 is free; verify `.env` is configured |
| **Frontend build errors** | Delete `node_modules` and run `npm install` again |
| **Database errors** | Re-run `seed_data.py`; check `DATABASE_URL` in `.env` |

---

## 📄 License

This project is for academic/educational purposes.

Built with ❤️ using FastAPI · React · FaceNet · Supabase
