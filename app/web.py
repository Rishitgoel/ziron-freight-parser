"""
FastAPI Web Application & Interactive Ziron LoadPilot Broker Triage Dashboard.
Provides:
  - Interactive Web Dashboard styled with the authentic Ziron Labs design system
  - REST API endpoint: POST /api/v1/parse
  - Health check: GET /api/v1/health
  - Interactive Swagger Docs: /docs
"""

import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.main import process_document
from app.models import DecisionResult

app = FastAPI(
    title="Ziron Labs Freight Intelligence API",
    description="Autonomous operational document parsing, deterministic validation, and decision routing engine.",
    version="1.0.0",
)


class ParseRequest(BaseModel):
    raw_text: str = Field(
        description="Unstructured raw text from freight rate confirmation, invoice, or shipping order"
    )
    model: Optional[str] = Field(
        default=None,
        description="OpenAI model name (e.g. gpt-4o-mini or gpt-4o)",
    )
    force_mock: bool = Field(
        default=False,
        description="If True, bypasses external API and uses the deterministic offline extractor",
    )


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ziron-freight-parser",
        "version": "1.0.0",
        "product": "LoadPilot",
    }


@app.post("/api/v1/parse", response_model=DecisionResult)
def parse_and_validate(request: ParseRequest):
    if not request.raw_text.strip():
        raise HTTPException(status_code=400, detail="Document text cannot be empty.")

    result = process_document(
        raw_text=request.raw_text,
        model=request.model,
        force_mock=request.force_mock,
    )
    return result


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ziron Labs | LoadPilot Document Intelligence</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Plus Jakarta Sans', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            background: '#090d16',
            card: '#0f172a',
            border: 'rgba(255, 255, 255, 0.08)',
            brand: {
              blue: '#3b6dff',
              indigo: '#5b4bff',
              violet: '#7c3aed',
            }
          }
        }
      }
    }
  </script>
  <style>
    body {
      background-color: #080c15;
      color: #f1f5f9;
      background-image: 
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(91, 75, 255, 0.15), transparent 70%),
        radial-gradient(ellipse 60% 40% at 90% 80%, rgba(59, 109, 255, 0.08), transparent 60%);
      background-attachment: fixed;
    }
    .ziron-gradient-text {
      background: linear-gradient(135deg, #3b6dff 0%, #7c3aed 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .ziron-btn {
      background: linear-gradient(135deg, #3b6dff 0%, #5b4bff 55%, #7c3aed 100%);
      box-shadow: 0 0 24px -4px rgba(124, 58, 237, 0.5);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .ziron-btn:hover {
      box-shadow: 0 0 32px 0px rgba(124, 58, 237, 0.7);
      transform: translateY(-1px);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }
    .glass-card-subtle {
      background: rgba(30, 41, 59, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .glow-crimson {
      box-shadow: 0 0 20px -4px rgba(239, 68, 68, 0.3);
      border-color: rgba(239, 68, 68, 0.4);
    }
    .glow-emerald {
      box-shadow: 0 0 20px -4px rgba(16, 185, 129, 0.3);
      border-color: rgba(16, 185, 129, 0.4);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col font-sans selection:bg-brand-violet selection:text-white">

  <!-- Navigation Bar -->
  <header class="border-b border-border/60 sticky top-0 z-50 backdrop-blur-xl bg-background/80">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Authentic Ziron Labs Z Logo -->
        <svg viewBox="0 0 100 100" class="w-8 h-8 shrink-0" role="img" aria-label="Ziron Labs">
          <defs>
            <linearGradient id="ziron-z" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#3b6dff"></stop>
              <stop offset="55%" stop-color="#5b4bff"></stop>
              <stop offset="100%" stop-color="#7c3aed"></stop>
            </linearGradient>
          </defs>
          <path d="M14 14 H86 V31 H14 Z" fill="url(#ziron-z)"></path>
          <path d="M86 31 L60 31 L14 69 L40 69 Z" fill="url(#ziron-z)"></path>
          <path d="M14 69 H86 V86 H14 Z" fill="url(#ziron-z)"></path>
        </svg>
        <div class="flex flex-col leading-none">
          <div class="flex items-center gap-2">
            <span class="text-base font-extrabold tracking-[0.22em] text-white">ZIRON</span>
            <span class="text-[9px] font-bold tracking-[0.4em] ziron-gradient-text">LABS</span>
          </div>
          <span class="text-[10px] text-slate-400 font-medium tracking-wider mt-0.5">LOADPILOT CORE</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <a href="/docs" target="_blank" class="text-xs text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-border bg-white/5 transition flex items-center gap-1.5 font-medium">
          <svg class="w-3.5 h-3.5 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          API Swagger Docs
        </a>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Pipeline Live
        </div>
      </div>
    </div>
  </header>

  <!-- Hero Header -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-md text-xs font-semibold uppercase tracking-wider bg-brand-violet/20 text-indigo-300 border border-brand-violet/30 mb-2">
          <span>Freight Document Intelligence</span>
          <span class="text-slate-500">•</span>
          <span class="text-slate-400">Pydantic v2 + OpenAI Structured Outputs</span>
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold tracking-tight text-white">
          Operational Document Triage
        </h1>
        <p class="text-sm text-slate-400 mt-1 max-w-2xl">
          Automates the extraction of unstructured rate confirmations, executes deterministic business validation rules, and drives human-in-the-loop decision routing.
        </p>
      </div>

      <!-- Quick Preset Buttons -->
      <div class="flex flex-wrap items-center gap-2 bg-slate-900/60 p-1.5 rounded-xl border border-border">
        <span class="text-xs text-slate-400 px-2 font-medium">Presets:</span>
        <button onclick="loadPreset('sample')" class="px-2.5 py-1 text-xs rounded-lg bg-brand-violet/20 hover:bg-brand-violet/30 text-indigo-200 border border-brand-violet/40 transition font-medium">
          ⚡ Sample Doc (Flagged)
        </button>
        <button onclick="loadPreset('clean')" class="px-2.5 py-1 text-xs rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition font-medium">
          ✓ Clean Load (Approved)
        </button>
        <button onclick="loadPreset('incomplete')" class="px-2.5 py-1 text-xs rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 transition font-medium">
          ⚠ Incomplete Doc
        </button>
      </div>
    </div>

    <!-- Main Workspace Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- Left Column: Raw Document Input -->
      <div class="lg:col-span-5 flex flex-col gap-4">
        <div class="glass-card rounded-2xl p-5 flex flex-col h-full shadow-xl">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <svg class="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              Raw Document Input
            </h2>
            <span class="text-[11px] text-slate-500 font-mono" id="char-count">0 chars</span>
          </div>

          <textarea 
            id="raw-input" 
            rows="16"
            class="w-full flex-1 p-3.5 rounded-xl bg-slate-950/70 border border-border text-slate-200 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-violet/50 focus:border-transparent leading-relaxed resize-none"
            placeholder="Paste freight rate confirmation or load agreement text here..."
          ></textarea>

          <div class="mt-4 pt-4 border-t border-border/60 flex flex-col sm:flex-row items-center justify-between gap-3">
            <label class="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
              <input type="checkbox" id="mock-toggle" class="rounded bg-slate-800 border-border text-brand-violet focus:ring-0">
              <span>Force Offline Fallback</span>
            </label>

            <button 
              id="submit-btn" 
              onclick="runPipeline()"
              class="w-full sm:w-auto ziron-btn px-5 py-2.5 rounded-xl text-white text-xs font-semibold flex items-center justify-center gap-2"
            >
              <svg id="btn-spinner" class="hidden w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <span id="btn-text">Execute Extraction & Rules</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column: Live Decision & Extracted Triage View -->
      <div class="lg:col-span-7 flex flex-col gap-4">

        <!-- Status & Decision Banner -->
        <div id="status-card" class="glass-card rounded-2xl p-6 transition-all duration-300">
          <div class="flex items-start justify-between gap-4">
            <div>
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Automated Decision Outcome</span>
              <div id="status-badge" class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
                <span>AWAITING INPUT</span>
              </div>
            </div>
            <div id="telemetry-badge" class="text-right text-[11px] font-mono text-slate-500">
              Ready
            </div>
          </div>

          <div id="summary-text" class="mt-3 text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-border/40 font-mono">
            Click 'Execute Extraction & Rules' or choose a preset to process the document through the intelligence pipeline.
          </div>
        </div>

        <!-- Discrepancy Breakdown Section (Shown when Flagged) -->
        <div id="anomalies-section" class="hidden space-y-3">
          <!-- Populated dynamically via JS -->
        </div>

        <!-- Structured Data Cards Grid -->
        <div class="glass-card rounded-2xl p-5">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center justify-between">
            <span>Structured Data Contract</span>
            <span class="text-[10px] font-mono text-brand-blue">FreightDocument Schema</span>
          </h2>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <!-- Carrier & Load -->
            <div class="glass-card-subtle p-3.5 rounded-xl">
              <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Carrier Name</span>
              <span id="field-carrier" class="text-sm font-bold text-white block mt-0.5 truncate">--</span>
            </div>

            <div class="glass-card-subtle p-3.5 rounded-xl">
              <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Load / Reference #</span>
              <span id="field-load" class="text-sm font-mono font-bold text-indigo-300 block mt-0.5 truncate">--</span>
            </div>

            <!-- Locations -->
            <div class="glass-card-subtle p-3.5 rounded-xl">
              <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Pickup Facility</span>
              <span id="field-pickup" class="text-xs font-medium text-slate-200 block mt-1">--</span>
            </div>

            <div class="glass-card-subtle p-3.5 rounded-xl">
              <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Delivery Facility</span>
              <span id="field-delivery" class="text-xs font-medium text-slate-200 block mt-1">--</span>
            </div>

            <!-- Financials Matrix -->
            <div class="glass-card-subtle p-3.5 rounded-xl sm:col-span-2">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Financial Breakdown</span>
                <span id="math-pill" class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">Pending</span>
              </div>
              <div class="grid grid-cols-3 gap-2 text-center pt-1 border-t border-border/40">
                <div class="p-2 rounded-lg bg-slate-950/40">
                  <span class="text-[10px] text-slate-500 block">Linehaul Rate</span>
                  <span id="field-linehaul" class="text-xs font-mono font-bold text-white">--</span>
                </div>
                <div class="p-2 rounded-lg bg-slate-950/40">
                  <span class="text-[10px] text-slate-500 block">Fuel (FSC)</span>
                  <span id="field-fsc" class="text-xs font-mono font-bold text-white">--</span>
                </div>
                <div class="p-2 rounded-lg bg-slate-950/40">
                  <span class="text-[10px] text-slate-500 block">Total Agreed</span>
                  <span id="field-total" class="text-xs font-mono font-bold text-indigo-300">--</span>
                </div>
              </div>
            </div>

            <!-- Weight -->
            <div class="glass-card-subtle p-3.5 rounded-xl sm:col-span-2">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Gross Cargo Weight</span>
                <span id="field-weight" class="text-xs font-mono font-bold text-white">--</span>
              </div>
              <div class="w-full bg-slate-800 rounded-full h-2 mt-2 overflow-hidden relative">
                <div id="weight-bar" class="h-2 rounded-full transition-all duration-500 bg-brand-blue" style="width: 0%"></div>
              </div>
              <div class="flex justify-between text-[9px] text-slate-500 mt-1 font-mono">
                <span>0 lbs</span>
                <span>Standard Limit: 45,000 lbs</span>
                <span>80,000 lbs (Max GVW)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Human-in-the-Loop Actions & JSON Drawer -->
        <div class="flex items-center justify-between gap-3 pt-1">
          <button onclick="toggleJson()" class="text-xs text-slate-400 hover:text-white px-3 py-2 rounded-xl border border-border bg-slate-900/50 transition font-mono flex items-center gap-1.5">
            <span>{ }</span> View Raw JSON Payload
          </button>
          
          <div class="flex items-center gap-2">
            <button onclick="alert('Permit sign-off recorded in broker audit log.')" class="text-xs px-3.5 py-2 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 transition font-semibold">
              Approve with Permit
            </button>
            <button onclick="alert('Rate amendment request drafted to carrier dispatch.')" class="text-xs px-3.5 py-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 transition font-semibold">
              Amend Rate
            </button>
          </div>
        </div>

        <!-- Raw JSON Modal / Container -->
        <div id="json-container" class="hidden glass-card rounded-2xl p-4 mt-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-mono text-slate-400">Canonical Output Payload</span>
            <button onclick="copyJson()" class="text-[11px] text-indigo-300 hover:underline">Copy JSON</button>
          </div>
          <pre id="json-output" class="p-3 rounded-xl bg-slate-950 text-emerald-400 text-xs font-mono overflow-x-auto max-h-60 leading-relaxed"></pre>
        </div>

      </div>
    </div>
  </main>

  <script>
    const PRESETS = {
      sample: `===================================================
FREIGHT RATE CONFIRMATION & ORDER AGREEMENT
===================================================
Ref #: LD-994821
Carrier: Apex Logistics Solutions LLC
Date: 10/12/2025
PICKUP DETAILS:
Origin: Distribution Center 4, Dallas, TX 75201
Date: Oct 14, 2025 @ 08:00 CST
DROP-OFF DETAILS:
Destination: Warehouse B, Atlanta, GA 30303
Date: Oct 16, 2025 @ 14:00 EST
CARGO DETAILS:
Description: Industrial Machinery Parts
Total Weight: 46,800 lbs (Gross)
FINANCIAL AGREEMENT:
Linehaul Rate: $2,200.00
Fuel Surcharge (FSC): $350.00
---------------------------------------------------
Total Agreed Amount: $2,800.00
Special Instructions: Driver must check in with security upon arrival. Call dispatch for unloading
door assignment.`,

      clean: `===================================================
FREIGHT RATE CONFIRMATION & ORDER AGREEMENT
===================================================
Ref #: LD-104928
Carrier: Swift Transport Solutions LLC
Date: 10/18/2025
PICKUP DETAILS:
Origin: Logistics Hub 1, Chicago, IL 60601
Date: Oct 20, 2025 @ 07:00 CST
DROP-OFF DETAILS:
Destination: Distribution Terminal C, Columbus, OH 43215
Date: Oct 21, 2025 @ 12:00 EST
CARGO DETAILS:
Description: Packaged Consumer Goods
Total Weight: 38,500 lbs (Gross)
FINANCIAL AGREEMENT:
Linehaul Rate: $2,000.00
Fuel Surcharge (FSC): $400.00
---------------------------------------------------
Total Agreed Amount: $2,400.00
Special Instructions: Standard dock delivery. Appointment confirmed.`,

      incomplete: `===================================================
FREIGHT RATE CONFIRMATION & ORDER AGREEMENT
===================================================
Ref #: PENDING_ASSIGNMENT
Carrier: 
Date: 10/22/2025
PICKUP DETAILS:
Origin: Dallas Facility
Date: Oct 25, 2025
DROP-OFF DETAILS:
Destination: Warehouse B, Atlanta, GA 30303
Date: Oct 27, 2025
CARGO DETAILS:
Description: Palletized Hardware
Total Weight: 32,000 lbs
FINANCIAL AGREEMENT:
Linehaul Rate: $1,500.00
Fuel Surcharge (FSC): $250.00
---------------------------------------------------
Total Agreed Amount: $1,750.00
Special Instructions: Check in with dispatch.`
    };

    function loadPreset(name) {
      document.getElementById('raw-input').value = PRESETS[name];
      updateCharCount();
      runPipeline();
    }

    function updateCharCount() {
      const len = document.getElementById('raw-input').value.length;
      document.getElementById('char-count').innerText = `${len} chars`;
    }

    document.getElementById('raw-input').addEventListener('input', updateCharCount);

    let lastResult = null;

    async function runPipeline() {
      const rawText = document.getElementById('raw-input').value;
      if (!rawText.trim()) {
        alert("Please paste document text or choose a preset.");
        return;
      }

      const forceMock = document.getElementById('mock-toggle').checked;
      const btn = document.getElementById('submit-btn');
      const spinner = document.getElementById('btn-spinner');
      const btnText = document.getElementById('btn-text');

      btn.disabled = true;
      spinner.classList.remove('hidden');
      btnText.innerText = "Extracting & Validating...";

      try {
        const response = await fetch('/api/v1/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            raw_text: rawText,
            force_mock: forceMock
          })
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const result = await response.json();
        lastResult = result;
        renderResult(result);
      } catch (err) {
        alert("Extraction failed: " + err.message);
      } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
        btnText.innerText = "Execute Extraction & Rules";
      }
    }

    function renderResult(res) {
      const statusCard = document.getElementById('status-card');
      const statusBadge = document.getElementById('status-badge');
      const summaryText = document.getElementById('summary-text');
      const telemetryBadge = document.getElementById('telemetry-badge');
      const anomaliesSection = document.getElementById('anomalies-section');

      // Update Decision Banner
      statusCard.classList.remove('glow-crimson', 'glow-emerald');
      if (res.status === 'APPROVED') {
        statusCard.classList.add('glow-emerald');
        statusBadge.className = "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
        statusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> APPROVED (STRAIGHT-THROUGH)';
      } else {
        statusCard.classList.add('glow-crimson');
        statusBadge.className = "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/40";
        statusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-red-400 animate-pulse"></span> FLAGGED FOR HUMAN REVIEW';
      }

      summaryText.innerText = res.summary;
      telemetryBadge.innerHTML = `Latency: <b>${res.metadata.processing_time_ms || 0} ms</b><br><span class="text-[10px] text-slate-500">${res.metadata.model || 'model'}</span>`;

      // Render Anomalies Breakdown
      anomaliesSection.innerHTML = '';
      if (res.validation.errors.length > 0 || res.validation.warnings.length > 0) {
        anomaliesSection.classList.remove('hidden');
        
        res.validation.errors.forEach(err => {
          const div = document.createElement('div');
          div.className = "p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-start gap-2.5";
          div.innerHTML = `<span class="px-2 py-0.5 rounded font-mono font-bold bg-red-500/20 text-red-400 shrink-0 text-[10px] uppercase">${err.code}</span> <span>${err.message}</span>`;
          anomaliesSection.appendChild(div);
        });

        res.validation.warnings.forEach(warn => {
          const div = document.createElement('div');
          div.className = "p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex items-start gap-2.5";
          div.innerHTML = `<span class="px-2 py-0.5 rounded font-mono font-bold bg-amber-500/20 text-amber-400 shrink-0 text-[10px] uppercase">${warn.code}</span> <span>${warn.message}</span>`;
          anomaliesSection.appendChild(div);
        });
      } else {
        anomaliesSection.classList.add('hidden');
      }

      // Populate Data Fields
      const d = res.data;
      document.getElementById('field-carrier').innerText = d.carrier_name || 'MISSING';
      document.getElementById('field-carrier').className = d.carrier_name ? 'text-sm font-bold text-white block mt-0.5 truncate' : 'text-sm font-bold text-red-400 block mt-0.5';

      document.getElementById('field-load').innerText = d.load_number || 'MISSING';
      document.getElementById('field-load').className = d.load_number ? 'text-sm font-mono font-bold text-indigo-300 block mt-0.5 truncate' : 'text-sm font-bold text-red-400 block mt-0.5';

      const pLoc = d.pickup_location;
      document.getElementById('field-pickup').innerText = (pLoc && pLoc.city && pLoc.state && pLoc.zip) 
        ? `${pLoc.city}, ${pLoc.state} ${pLoc.zip}` 
        : (pLoc ? JSON.stringify(pLoc) : 'MISSING');

      const dLoc = d.delivery_location;
      document.getElementById('field-delivery').innerText = (dLoc && dLoc.city && dLoc.state && dLoc.zip) 
        ? `${dLoc.city}, ${dLoc.state} ${dLoc.zip}` 
        : (dLoc ? JSON.stringify(dLoc) : 'MISSING');

      document.getElementById('field-linehaul').innerText = d.total_linehaul_rate ? `$${d.total_linehaul_rate.toLocaleString('en-US', {minimumFractionDigits: 2})}` : 'MISSING';
      document.getElementById('field-fsc').innerText = d.fuel_surcharge !== null ? `$${d.fuel_surcharge.toLocaleString('en-US', {minimumFractionDigits: 2})}` : 'MISSING';
      document.getElementById('field-total').innerText = d.total_pay ? `$${d.total_pay.toLocaleString('en-US', {minimumFractionDigits: 2})}` : 'MISSING';

      // Math Pill
      const mathPill = document.getElementById('math-pill');
      if (res.validation.errors.some(e => e.code === 'RATE_MISMATCH')) {
        mathPill.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30";
        mathPill.innerText = "RATE MISMATCH";
      } else if (d.total_linehaul_rate !== null && d.fuel_surcharge !== null && d.total_pay !== null) {
        mathPill.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
        mathPill.innerText = "MATH BALANCED";
      } else {
        mathPill.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400";
        mathPill.innerText = "INCOMPLETE";
      }

      // Weight bar
      const weight = d.weight_lbs || 0;
      document.getElementById('field-weight').innerText = `${weight.toLocaleString()} lbs`;
      const weightPercent = Math.min(100, Math.round((weight / 60000) * 100));
      const weightBar = document.getElementById('weight-bar');
      weightBar.style.width = `${weightPercent}%`;
      if (weight > 45000) {
        weightBar.className = "h-2 rounded-full transition-all duration-500 bg-amber-400";
      } else {
        weightBar.className = "h-2 rounded-full transition-all duration-500 bg-brand-blue";
      }

      // Populate JSON Output
      document.getElementById('json-output').innerText = JSON.stringify(res, null, 2);
    }

    function toggleJson() {
      const c = document.getElementById('json-container');
      c.classList.toggle('hidden');
    }

    function copyJson() {
      if (lastResult) {
        navigator.clipboard.writeText(JSON.stringify(lastResult, null, 2));
        alert("JSON copied to clipboard!");
      }
    }

    // Auto-load sample document on first page open
    window.addEventListener('DOMContentLoaded', () => {
      loadPreset('sample');
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return DASHBOARD_HTML


if __name__ == "__main__":
    import uvicorn
    print("\nStarting Ziron Labs LoadPilot Web Dashboard at http://localhost:8000")
    print("Swagger API documentation available at http://localhost:8000/docs\n")
    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=True)
