# RevGuard — Vercel Deployment Guide

This guide walks you through deploying **RevGuard** to [Vercel](https://vercel.com) using **Option A: Fullstack Monorepo Deployment** (Vite React frontend + FastAPI Python Serverless Backend on the same domain).

---

## Architecture on Vercel

```
┌─────────────────────────────────────────────────────────────┐
│                    VERCEL EDGE ROUTER                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    /api/*  &  /docs                        /* (All other routes)
┌─────────────────────────────┐   ┌───────────────────────────┐
│  Serverless Python Function │   │   Vite React Static SPA   │
│       (@vercel/python)      │   │     (frontend/dist)       │
│        [api/index.py]       │   │    [/cockpit, /cases,     │
│       FastAPI Backend       │   │     /review, /docs]       │
└─────────────────────────────┘   └───────────────────────────┘
```

* **Zero CORS issues**: Frontend and Backend share the same domain (`https://<your-project>.vercel.app`).
* **FastAPI documentation**: Interactive Swagger docs available at `https://<your-project>.vercel.app/docs`.
* **SPA Routing**: Client-side routes like `/cockpit`, `/cases`, and `/review` don't 404 on page refresh.

---

## Step 1: Push Repository to GitHub

Ensure your latest code with Vercel configuration is committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "feat: configure Vercel fullstack monorepo deployment"
git push origin main
```

---

## Step 2: Import Project in Vercel

1. Log in to [vercel.com](https://vercel.com).
2. Click **"Add New..."** → **"Project"**.
3. Select your **`RazorPayHackathon`** GitHub repository and click **Import**.
4. **Project Settings**:
   * **Root Directory**: Leave as `./` (Root directory).
   * **Framework Preset**: Leave as **Other** (or Vite). The root `vercel.json` and `package.json` will automatically build the frontend into `frontend/dist` and deploy Python serverless functions from `api/index.py`.

---

## Step 3: Configure Environment Variables

In the Vercel project configuration page (under **Environment Variables**), add the following keys:

| Variable Name | Required? | Description / Example |
|---|:---:|---|
| `FIRESTORE_PROJECT_ID` | **Yes** | Your Firebase Project ID (e.g., `rev-gaurd-2026`) |
| `FIREBASE_CREDENTIALS_JSON` | **Yes** | The **entire contents** of your Firebase Service Account JSON file pasted as a string (see formatting tip below) |
| `GEMINI_API_KEY` | **Yes** | Google AI Studio API key for Gemini |
| `GEMINI_MODEL` | No | Default: `gemini-flash-latest` or `gemini-1.5-flash` |
| `RAZORPAY_KEY_ID` | **Yes** | Razorpay Test Key ID (`rzp_test_...`) |
| `RAZORPAY_KEY_SECRET` | **Yes** | Razorpay Test Key Secret |
| `MESSAGING_PROVIDER` | No | `twilio` (for real WhatsApp) or `mock` (default) |
| `TWILIO_ACCOUNT_SID` | If Twilio | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | If Twilio | Twilio Auth Token |
| `TWILIO_WHATSAPP_NUMBER` | If Twilio | `whatsapp:+14155238886` |
| `POLICY_MAX_AMOUNT_AUTO` | No | Default: `1000000` (paise = ₹10,000) |
| `POLICY_MIN_CONFIDENCE_AUTO`| No | Default: `0.85` |
| `POLICY_MAX_RETRY_AUTO` | No | Default: `3` |

### 💡 Tip: Formatting `FIREBASE_CREDENTIALS_JSON`
Open your `rev-gaurd-firebase-adminsdk-*.json` file, copy the entire JSON object `{ "type": "service_account", ... }`, and paste it directly into Vercel's value field. Vercel supports multiline JSON strings seamlessly.

*(Alternative: You can also base64 encode the file content and set `FIREBASE_SERVICE_ACCOUNT_KEY` to the base64 string.)*

---

## Step 4: Deploy & Verify

1. Click **"Deploy"**.
2. Once the build completes, Vercel will provide your live deployment URL:
   `https://<your-project>.vercel.app`

### Post-Deployment Verification Checklist:
- [ ] **Landing Page**: Visit `https://<your-project>.vercel.app/`
- [ ] **Operator Cockpit**: Visit `https://<your-project>.vercel.app/cockpit`
- [ ] **API Health Check**: Visit `https://<your-project>.vercel.app/api/health` → should return `{"status":"ok","service":"revguard-api"}`
- [ ] **Swagger Interactive Docs**: Visit `https://<your-project>.vercel.app/docs`
- [ ] **Seed Live Telemetry**: On the Cockpit screen, click **`⚡ SEED DEMO TELEMETRY`** to verify live Firestore database read/write.
- [ ] **Run 60-Sec Judge Demo**: Click **`▶ 60-SEC JUDGE DEMO`** to execute the end-to-end autonomous recovery sequence live on Vercel.

---

## Option B: Standalone Frontend Deployment (Alternative)

If you ever prefer to run the FastAPI backend on a dedicated container (e.g. Render / Railway / Google Cloud Run) and only host the React frontend on Vercel:

1. In Vercel Project Settings, set **Root Directory** to `frontend`.
2. Framework Preset will be automatically detected as **Vite**.
3. Under Environment Variables, add:
   * `VITE_API_URL`: `https://<your-backend-api-domain>`
4. Deploy! Client-side routing will work out of the box using `frontend/vercel.json`.
