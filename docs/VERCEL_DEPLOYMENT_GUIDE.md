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

### ⚡ Quickest Way: Copy & Paste Your `.env` File!

You don't need to type variables one by one. Vercel supports bulk `.env` pasting:

1. Open your project's local [`.env`](file:///d:/RazorPayHackathon/.env) file.
2. Select all text (`Ctrl + A`) and copy (`Ctrl + C`). *(We have already embedded `FIREBASE_CREDENTIALS_JSON` inside it!)*
3. In Vercel's **Environment Variables** section, click into the very first **"Key"** input box and press **`Ctrl + V`**.
4. Vercel will automatically parse every line into the key-value table instantly!
5. Click **"Save"** or continue to Deploy.

> [!TIP]
> Your `.env` already has `FIREBASE_CREDENTIALS_JSON` populated with your service account key. You can safely leave or remove `GOOGLE_APPLICATION_CREDENTIALS` since RevGuard automatically uses `FIREBASE_CREDENTIALS_JSON` in the cloud.

---

### Reference Table (For Manual Check)

| Variable Name | Required? | Description / Example |
|---|:---:|---|
| `FIRESTORE_PROJECT_ID` | **Yes** | `rev-gaurd` |
| `FIREBASE_CREDENTIALS_JSON` | **Yes** | Single-line JSON string of service account key (already in your `.env`) |
| `GEMINI_API_KEY` | **Yes** | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-flash-latest` |
| `RAZORPAY_KEY_ID` | **Yes** | Razorpay Test Key ID (`rzp_test_...`) |
| `RAZORPAY_KEY_SECRET` | **Yes** | Razorpay Test Key Secret |
| `RAZORPAY_WEBHOOK_SECRET` | No | `revguard_webhook_secret_123` |
| `MESSAGING_PROVIDER` | No | `twilio` or `mock` |
| `TWILIO_ACCOUNT_SID` | If Twilio | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | If Twilio | Twilio Auth Token |
| `TWILIO_WHATSAPP_NUMBER` | If Twilio | `whatsapp:+14155238886` |
| `TWILIO_TEST_PHONE_OVERRIDE`| If Twilio | e.g. `+917355788131` |
| `POLICY_MAX_AMOUNT_AUTO` | No | `1000000` (paise = ₹10,000) |
| `POLICY_MIN_CONFIDENCE_AUTO`| No | `0.85` |
| `POLICY_MAX_RETRY_AUTO` | No | `3` |

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
