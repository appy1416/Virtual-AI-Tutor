# EduTwin AI Frontend - React App

This is the user interface for the EduTwin AI Companion. It is a single-page application built using React, bundled with Vite, and styled using Tailwind CSS for premium, responsive layouts.

## Directory Structure

```text
frontend/
├── src/
│   ├── assets/       # Styles, images, custom fonts
│   ├── components/   # Atomic UI elements (Buttons, Forms, Alerts)
│   ├── context/      # React contexts (Global authentication, Theme)
│   ├── hooks/        # Custom react hooks (useChat, useSpeech)
│   ├── layouts/      # Layout containers for routes (Dashboard, Auth)
│   ├── pages/        # Views (Login, Dashboard, Chat Interface, Analytics)
│   ├── services/     # API request hooks, WebSocket connection clients
│   ├── styles/       # Tailwind directive files
│   └── utils/        # Helper scripts (formatting, token validation)
├── package.json      # Dependencies and execution commands
├── tailwind.config.js# Tailwind theme configuration
├── index.html        # Main HTML layout entrypoint
└── README.md         # This manual
```

---

## Local Setup Instructions (Without Docker)

### 1. Install Node.js Dependencies
Navigate to the directory and run:
```bash
cd frontend
npm install
```

### 2. Configure Environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to ensure `VITE_API_URL` points to your active FastAPI backend.

### 3. Run Development Server
```bash
npm run dev
```
The application will launch on `http://localhost:5173`.

### 4. Build for Production
Create an optimized production build in the `dist` directory:
```bash
npm run build
```

---

## Design Guidelines

- **Typography**: Clean, professional type scaling using Google Fonts (e.g., 'Inter' or 'Outfit').
- **Colors**: Vibrant dark modes, custom HSL gradients (royal blue to neon indigo), and clean card structures.
- **Components**: Component styling must be driven by Tailwind variables defined in `tailwind.config.js` to ensure consistent brand appearance.
- **Interactions**: Subtle hover micro-animations on cards and buttons. Smooth transitions for page changes.
