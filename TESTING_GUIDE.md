# Testing Guide - Climate Research Web Dashboard

Complete guide to test all features of the web dashboard.

## Prerequisites

Make sure Flask is installed:
```bash
pip install Flask==3.0.0
```

## Step 1: Start the Web Server

```bash
cd /home/user/FC
python climate_research_system/web/app.py
```

You should see:
```
======================================================================
  Climate Research Agent Orchestration System - Web Dashboard
======================================================================

  Dashboard URL: http://localhost:5000
  Registered Agents: 1

  Press Ctrl+C to stop the server
======================================================================

 * Running on http://127.0.0.1:5000
```

✅ **Server is running!**

## Step 2: Test Dashboard Page

### Open in Browser
```
http://localhost:5000
```

### What to Test:

#### A. Statistics Cards
- [ ] See 4 stat cards at top
- [ ] "Total Agents" shows **1**
- [ ] "Enabled" shows **1**
- [ ] "Completed Research" shows **1** (from our earlier test)
- [ ] "System Uptime" shows time since server started

#### B. Agent Card
- [ ] See card titled "Climate Data Agent"
- [ ] Status badge shows "idle" (blue)
- [ ] Shows ID: `climate_001`
- [ ] Shows Messages: 0 (or higher if you ran tests)
- [ ] Shows Errors: 0

#### C. Toggle Agent (MOST IMPORTANT!)
1. Click **"⏸️ Disable"** button
   - [ ] Button changes to **"▶️ Enable"** (green)
   - [ ] Agent card becomes semi-transparent (opacity 0.6)
   - [ ] Status badge changes to "disabled" (gray)
   - [ ] Notification appears: "Agent disabled successfully"
   - [ ] "Enabled Agents" stat changes to **0**

2. Click **"▶️ Enable"** button
   - [ ] Button changes back to **"⏸️ Disable"** (yellow)
   - [ ] Agent card becomes fully visible
   - [ ] Status badge changes to "idle" (blue)
   - [ ] Notification appears: "Agent enabled successfully"
   - [ ] "Enabled Agents" stat changes to **1**

#### D. Reset Agent
1. Click **"🔄 Reset"** button
2. Confirm the dialog
   - [ ] Notification appears: "Agent reset successfully"
   - [ ] Message count resets to 0

#### E. Auto-Refresh
- [ ] Wait 30 seconds
- [ ] Page automatically refreshes (you'll see network activity)

## Step 3: Test Research Page

### Navigate
Click **"Research"** in the navigation bar or go to:
```
http://localhost:5000/research
```

### What to Test:

#### A. Form Fields
- [ ] See "City" input field
- [ ] See "Country" input field
- [ ] See "Climate Data Period" (default: 30)
- [ ] See "Include climate projections" checkbox (checked)

#### B. Sidebar - Active Agents
- [ ] Right sidebar shows "Active Agents"
- [ ] Shows "Climate Data Agent" with checkmark ✓
- [ ] Shows status "idle"

#### C. Sidebar - Recent Research
- [ ] Shows "Recent Research" section
- [ ] Shows "Berlin, Germany" from our test
- [ ] Click on it to go to results (optional)

#### D. Start Research
1. Fill in form:
   - City: **Paris**
   - Country: **France**
   - Keep defaults

2. Click **"🔬 Start Research"**
   - [ ] Button changes to "⏳ Researching..."
   - [ ] Button is disabled while running
   - [ ] After ~1 second, research completes
   - [ ] Notification: "Research completed for Paris, France"

3. Check results card appears below:
   - [ ] Shows "📊 Paris, France"
   - [ ] Shows Research ID: `paris_france`
   - [ ] Shows completion timestamp
   - [ ] Progress bar showing completeness (likely 50% because of mock data)
   - [ ] Shows "Agents Used: 1 / 1"
   - [ ] Validation status badge
   - [ ] Recommendations (likely: "Data completeness below 70%...")

4. Test Result Actions:
   - [ ] Click **"📄 View Full Results"** → Goes to Results page
   - [ ] Click **"💾 Download JSON"** → Downloads paris_france.json

#### E. Try with Disabled Agent
1. Go back to Dashboard
2. Disable the Climate Data Agent
3. Go to Research page
4. Try to start research
   - [ ] Error notification: "No agents are enabled"

5. Re-enable the agent before continuing

## Step 4: Test Results Page

### Navigate
Click **"Results"** in navigation or go to:
```
http://localhost:5000/results
```

### What to Test:

#### A. Results Table
- [ ] See table with research results
- [ ] Should have at least 2 rows (Berlin, Paris)
- [ ] Columns: City, Country, Completed, Agents, Completeness, Actions

#### B. View Details
1. Click **"View"** button on Paris research
   - [ ] Modal opens
   - [ ] Shows title "Paris, France"
   - [ ] Shows location details
   - [ ] Shows summary with progress bar
   - [ ] Shows validation report
   - [ ] Shows agent results section
   - [ ] Shows notes/warnings about missing data

2. Test modal actions:
   - [ ] Click **"💾 Download JSON"** → Downloads file
   - [ ] Click **"Close"** or X → Modal closes
   - [ ] Click outside modal → Modal closes

#### C. Direct Download
- [ ] Click **"Download"** button in table
- [ ] JSON file downloads

#### D. Refresh
- [ ] Click **"🔄 Refresh"** button
- [ ] Table reloads

## Step 5: Test API Endpoints

You can test the API using `curl` commands:

### A. Get All Agents
```bash
curl http://localhost:5000/api/agents
```
Expected: JSON with agent list

### B. Toggle Agent
```bash
# Disable
curl -X POST http://localhost:5000/api/agents/climate_001/toggle

# Enable (run again)
curl -X POST http://localhost:5000/api/agents/climate_001/toggle
```

### C. Start Research via API
```bash
curl -X POST http://localhost:5000/api/research/start \
  -H "Content-Type: application/json" \
  -d '{"city": "Tokyo", "country": "Japan"}'
```

### D. List All Research
```bash
curl http://localhost:5000/api/research/list
```

### E. Get Specific Research
```bash
curl http://localhost:5000/api/research/paris_france
```

### F. Get Statistics
```bash
curl http://localhost:5000/api/stats
```

## Step 6: Test Edge Cases

### A. Invalid Research
1. Go to Research page
2. Leave City or Country empty
3. Click "Start Research"
   - [ ] Browser validation prevents submission

### B. Multiple Rapid Clicks
1. Click toggle button rapidly 3 times
   - [ ] Each click should complete
   - [ ] Final state should be correct

### C. Navigation
1. Click between pages
   - [ ] Dashboard → Research → Results → Dashboard
   - [ ] Active page highlighted in navigation
   - [ ] Data loads on each page

## Expected Limitations (Mock Data)

Since ClimateDataAgent uses **mock data**, you'll see:

✅ **What Works:**
- Agent registration and management
- Enable/disable functionality
- Research workflow execution
- Data persistence (JSON files)
- Validation reports
- UI interactions

⚠️ **What's Mock:**
- All climate metrics show `null` (no real API integration yet)
- Notes show "Missing required metric" warnings
- Completeness is low (~50%)
- This is EXPECTED and correct!

## Files Generated During Testing

Check these directories:

```bash
# Research results
ls climate_research_system/data/

# Should see:
# - research_berlin_germany.json
# - research_paris_france.json
# - validation_berlin_germany.json
# - validation_paris_france.json
```

## Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing process
kill -9 <PID>

# Or use different port
# Edit app.py, change last line to:
# app.run(debug=True, host='0.0.0.0', port=8000)
```

### Flask not found
```bash
pip install Flask==3.0.0
```

### Can't access from other devices
- Server runs on `0.0.0.0` (all interfaces)
- Check firewall settings
- Access via: `http://<your-ip>:5000`

### Browser shows errors
- Open browser console (F12)
- Check for JavaScript errors
- Check Network tab for failed requests

## Success Criteria

✅ You've successfully tested the dashboard if:
1. [ ] Can view agents on dashboard
2. [ ] Can enable/disable agents with buttons
3. [ ] Can start research via web form
4. [ ] Can view results in table
5. [ ] Can open modal with detailed results
6. [ ] Can download JSON files
7. [ ] Notifications appear for actions
8. [ ] Statistics update correctly

## Next Steps After Testing

Once everything works:
1. **Add real API integrations** to ClimateDataAgent
2. **Create more agents** (Emissions, Vulnerability, etc.)
3. **Customize the UI** (colors, logo, etc.)
4. **Deploy to production** with Gunicorn
5. **Add authentication** if needed

## Video Walkthrough (Steps)

If you want to record a demo:
1. Start server
2. Show dashboard with agent
3. Toggle agent off/on
4. Go to Research, start Paris research
5. View results in table
6. Open modal to see details
7. Download JSON

Total time: ~2-3 minutes

Enjoy your Climate Research Dashboard! 🌍
