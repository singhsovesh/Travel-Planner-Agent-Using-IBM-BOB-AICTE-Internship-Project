# ✈ IBM Travel Planner Agent

An AI-powered Travel Planner Agent built with **IBM Granite** (via IBM watsonx.ai on IBM Cloud Lite) and Python/Flask.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 💬 **Chat Agent** | Conversational AI travel planning with session memory |
| 🌍 **Destination Suggestions** | IBM Granite recommends 5 destinations matching your preferences |
| 📖 **Place Explorer** | Detailed travel guides with local tips & hidden gems |
| 📅 **Itinerary Builder** | Day-by-day plans with morning/afternoon/evening activities + meals |
| 💰 **Budget Planner** | Detailed cost breakdowns per category |
| 🌤 **Weather Forecast** | Real-time 14-day forecast via Open-Meteo (no API key needed) |
| 🚀 **Transport Options** | Flight/train/bus comparisons with booking tips |
| 🏨 **Accommodation** | Hotel/hostel/Airbnb recommendations by area |
| 📋 **Visa Info** | Entry requirements, documents, health rules |
| 🎒 **Packing Lists** | Climate + activity-specific packing lists |
| 📁 **Booking Manager** | Create, track, and cancel travel bookings |
| 🛡 **Travel Alerts** | Safety advisories, health warnings, emergency contacts |

---

## 🛠 Technology Stack

- **AI/LLM**: IBM Granite (`ibm/granite-3-3-8b-instruct`) via [IBM watsonx.ai](https://www.ibm.com/watsonx) (IBM Cloud Lite)
- **Backend**: Python 3.11+ / Flask 3.0
- **Weather**: Open-Meteo API (free, no key required)
- **Geocoding**: OpenStreetMap Nominatim (free)
- **Frontend**: Vanilla HTML5/CSS3/JavaScript (IBM Carbon Design inspired)

---

## ⚙ Setup

### 1. Prerequisites

- Python 3.11+
- IBM Cloud account (free Lite tier works)
- IBM watsonx.ai project

### 2. IBM Cloud Setup

1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (free Lite tier)
2. Create a **Watson Machine Learning** service instance
3. Create a **watsonx.ai** project at [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
4. Copy your **API Key** and **Project ID**

### 3. Configure .env

Open `.env` and fill in your credentials:

```env
IBM_WATSONX_API_KEY=your_actual_api_key
IBM_WATSONX_PROJECT_ID=your_actual_project_id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 📁 Project Structure

```
Travel Agent AICTE/
├── .env                              # IBM Cloud credentials (configure this)
├── app.py                            # Flask REST API — all endpoints
├── config.py                         # Configuration loader
├── granite_client.py                 # IBM Granite LLM client (watsonx.ai)
├── chat_agent.py                     # Conversational AI agent
├── destination_service.py            # Destination suggestions & guides
├── itinerary_service.py              # Day-by-day itinerary builder
├── weather_service.py                # Open-Meteo weather integration
├── transport_accommodation_service.py# Transport & accommodation
├── booking_service.py                # Booking management & schedule optimizer
├── requirements.txt                  # Python dependencies
├── templates/
│   └── index.html                    # Main frontend (Jinja2 template)
└── static/
    ├── css/style.css                 # IBM Carbon-inspired styles
    └── js/app.js                     # Frontend JavaScript
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Chat with the AI travel agent |
| POST | `/api/chat/reset` | Reset conversation history |
| POST | `/api/destinations/suggest` | Suggest destinations |
| POST | `/api/destinations/describe` | Get destination guide |
| POST | `/api/destinations/local-tips` | Get local insider tips |
| POST | `/api/weather` | Get weather forecast |
| POST | `/api/itinerary/build` | Build full itinerary |
| POST | `/api/itinerary/optimize` | Optimize existing itinerary |
| POST | `/api/itinerary/budget` | Estimate travel budget |
| POST | `/api/transport` | Get transport options |
| POST | `/api/accommodation` | Get accommodation recommendations |
| POST | `/api/visa` | Get visa requirements |
| POST | `/api/packing-list` | Generate packing list |
| POST | `/api/alerts` | Get travel safety alerts |
| GET  | `/api/bookings` | List all bookings |
| POST | `/api/bookings` | Create a booking |
| GET  | `/api/bookings/<id>` | Get a booking |
| PUT  | `/api/bookings/<id>` | Update a booking |
| POST | `/api/bookings/<id>/cancel` | Cancel a booking |
| POST | `/api/bookings/<id>/alerts` | Add alert to booking |
| GET  | `/api/health` | Health & credentials status |

---

## 💡 Example Chat Queries

- *"Plan a 10-day trip to Japan in April with a moderate budget"*
- *"I want a beach holiday under $100/day, departing from London"*
- *"What's the weather like in Bali in August?"*
- *"What visa do I need as an Indian passport holder for Japan?"*
- *"Build a packing list for a winter trip to Iceland with hiking"*
- *"Suggest transport options from Paris to Amsterdam"*

---

## 📝 Notes

- The `.env` file contains sensitive credentials — never commit it to version control
- Weather data is real-time from Open-Meteo (free, no account needed)
- AI responses (destinations, itineraries, etc.) use IBM Granite via IBM Cloud Lite
- Bookings are stored in-memory; restart resets them (production use: add a database)
- Visa/safety info is AI-generated — always verify with official government sources
