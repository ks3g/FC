# Web Dashboard

Flask-based web interface for the Climate Research Agent Orchestration System.

## Features

### Dashboard (`/`)
- View all registered agents and their status
- Enable/disable agents with toggle buttons
- Reset agents to initial state
- Real-time statistics (total agents, enabled agents, research count, uptime)
- Auto-refresh every 30 seconds

### Research Page (`/research`)
- Start new climate research for any city
- Configure research parameters (data years, projections)
- View active agents
- See recent research
- View results immediately after completion

### Results Page (`/results`)
- Browse all completed research
- View detailed results in modal
- Download research data as JSON
- See validation reports and recommendations
- Track data completeness

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the web server:
```bash
python climate_research_system/web/app.py
```

3. Open browser to: http://localhost:5000

## API Endpoints

### Agent Management
- `GET /api/agents` - List all agents
- `GET /api/agents/<id>` - Get agent details
- `POST /api/agents/<id>/toggle` - Enable/disable agent
- `POST /api/agents/<id>/reset` - Reset agent

### Research
- `POST /api/research/start` - Start new research
- `GET /api/research/list` - List all research
- `GET /api/research/<id>` - Get research details
- `GET /api/research/<id>/download` - Download as JSON

### Statistics
- `GET /api/stats` - System statistics

## API Usage Examples

### Start Research
```bash
curl -X POST http://localhost:5000/api/research/start \
  -H "Content-Type: application/json" \
  -d '{"city": "Berlin", "country": "Germany"}'
```

### Toggle Agent
```bash
curl -X POST http://localhost:5000/api/agents/climate_001/toggle
```

### Get Research Results
```bash
curl http://localhost:5000/api/research/berlin_germany
```

## Architecture

```
web/
├── app.py                 # Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with nav
│   ├── dashboard.html    # Agent dashboard
│   ├── research.html     # Research form
│   └── results.html      # Results viewer
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Styles
    └── js/
        └── main.js       # JavaScript utilities
```

## Development

### Adding New Pages

1. Create HTML template in `templates/`
2. Add route in `app.py`
3. Add navigation link in `base.html`

### Adding New API Endpoints

1. Add route function in `app.py`
2. Return JSON response
3. Handle errors appropriately

### Customizing Styles

Edit `static/css/style.css` to customize colors, fonts, layouts.

## Production Deployment

For production, use a proper WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 climate_research_system.web.app:app
```

## Security Notes

- Change the SECRET_KEY in app.py for production
- Add authentication if deploying publicly
- Enable HTTPS for production
- Implement rate limiting for API endpoints

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Screenshots

(Add screenshots when available)

## Troubleshooting

**Port already in use:**
```bash
# Change port in app.py or use environment variable
export FLASK_RUN_PORT=8000
```

**Flask not found:**
```bash
pip install Flask
```

**Can't access from other devices:**
- Make sure host is set to '0.0.0.0' (already configured)
- Check firewall settings
