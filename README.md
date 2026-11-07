
# ✈️ Travel Planner Agent

### Your AI-powered travel companion, built with IBM Granite

**AICTE Edunet Foundation Project · Problem Statement No. 5**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![IBM
Granite](https://img.shields.io/badge/AI-IBM%20Granite-052FAD?logo=ibm&logoColor=white)](https://www.ibm.com/granite)
[![IBM
watsonx.ai](https://img.shields.io/badge/Platform-watsonx.ai-0F62FE?logo=ibm&logoColor=white)](https://www.ibm.com/products/watsonx-ai)
[![Project](https://img.shields.io/badge/Project-AICTE%20Edunet-0A66C2)](https://github.com/singhsovesh/Travel-Planner-Agent-Using-IBM-BOB-AICTE-Internship-Project)

*Plan smarter. Travel better. Explore more.*
:::

------------------------------------------------------------------------

## 📌 Project Overview

Travel planning often involves switching between multiple platforms to
research destinations, compare transport and accommodation options,
check weather conditions, estimate budgets, and organize an itinerary.

**Travel Planner Agent** is an AI-powered travel assistant designed to
bring these activities into one experience. It uses **IBM Granite
through IBM watsonx.ai** to understand travel-related questions and help
users explore destinations, create personalized trip plans, and get
practical travel guidance.

The project was developed in response to **AICTE Edunet Foundation
Problem Statement No. 5 -- Travel Planner Agent**, which focuses on
using AI and real-time information to make trip planning more efficient
and personalized.

## 🎯 Problem Statement

A Travel Planner Agent should help users plan trips efficiently and
intelligently. It should understand preferences, budgets, and
constraints; suggest destinations; build itineraries; and recommend
transport and accommodation options. Integrations such as maps, weather
updates, and local guides can make the experience more useful, while
booking support and schedule optimization can help simplify travel
management.

**Mandatory technology requirement:** IBM Cloud Lite services / IBM
Granite.

## ✨ Key Features

The application is designed around the following travel-planning
capabilities:

-   **AI travel chat** -- Ask travel-related questions using the IBM
    Granite-powered assistant.
-   **Personalized trip planning** -- Get help shaping an itinerary
    around destination preferences, trip duration, and budget.
-   **Destination discovery** -- Explore places to visit and get
    destination suggestions.
-   **Itinerary assistance** -- Organize travel ideas into a day-by-day
    plan.
-   **Transport guidance** -- Explore transport options for a trip.
-   **Accommodation guidance** -- Get help considering hotel and stay
    options.
-   **Weather information** -- Access weather-related travel guidance
    when the relevant API is configured.
-   **Budget estimation** -- Plan and compare travel costs.
-   **Currency assistance** -- Get help with travel currency questions.
-   **Visa and entry guidance** -- Find general visa and entry
    information to research before travelling.
-   **Packing suggestions** -- Get destination- and trip-related packing
    advice.
-   **Booking workflow** -- Access the application's booking and
    reservation-management features.

> Availability of live information depends on the relevant API
> credentials, service access, and configuration. AI-generated travel,
> visa, and safety information should be independently verified before
> making bookings or travel decisions.

## 🖥️ Application Preview

### Home page

The landing page introduces the travel assistant, highlights its
capabilities, and provides entry points for AI-assisted planning and
manual booking.

![Travel Planner Agent home
page](docs/images/travel-planner-homepage.png)

### AI travel chat

The chat interface lets users ask travel questions and receive responses
from the IBM Granite-powered assistant. The interface also displays
API/service status and suggested questions.

![Travel Planner Agent AI chat
interface](docs/images/travel-ai-chat.png)

## 🧠 AI Integration

The project integrates **IBM Granite** using **IBM watsonx.ai**.

At a high level, the interaction flow is:

1.  A user enters a travel question or planning request in the
    application.
2.  The Flask application receives the request through its backend
    route.
3.  The relevant agent/service prepares the request for the language
    model.
4.  IBM Granite is called through the watsonx.ai service using
    configured credentials.
5.  The generated response is returned to the application and displayed
    in the chat interface.

The application can also use configured external services for supporting
travel information, such as weather and maps/place data.

## 🧰 Technology Stack

  Area             Technology
  ---------------- ----------------------------------------------
  Backend          Python, Flask
  AI model         IBM Granite
  AI platform      IBM watsonx.ai
  Cloud platform   IBM Cloud Lite
  Frontend         HTML, CSS, JavaScript
  UI rendering     Jinja2 templates
  Weather data     OpenWeatherMap API (when configured)
  Maps / places    Google Maps Platform API (when configured)
  Dependencies     Python packages listed in `requirements.txt`

## 🗂️ Project Structure

``` text
Travel-Planner-Agent/
│
├── app.py
├── agents.py
├── chat_agent.py
├── granite_client.py
├── config.py
│
├── auth.py
├── models.py
├── booking_service.py
├── itinerary_service.py
├── destination_service.py
├── transport_accommodation_service.py
├── weather_service.py
├── currency_service.py
├── analytics_service.py
├── pdf_service.py
├── templates_service.py
│
├── templates/
│   ├── home.html
│   ├── index.html
│   ├── dashboard.html
│   ├── chat.html
│   ├── login.html
│   ├── register.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── icons/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*The structure above summarizes the main application modules and
folders; filenames may vary with the current project version.*

## ⚙️ Getting Started

### 1. Clone the repository

``` bash
git clone https://github.com/singhsovesh/Travel-Planner-Agent-Using-IBM-BOB-AICTE-Internship-Project.git
cd Travel-Planner-Agent-Using-IBM-BOB-AICTE-Internship-Project
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file by copying the example:

**Windows PowerShell:**

``` powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

``` bash
cp .env.example .env
```

Open `.env` and add your own credentials. Use the exact variable names
expected by the application and its configuration module.

Typical IBM watsonx.ai settings include:

``` env
IBM_API_KEY=your_ibm_cloud_api_key
IBM_CLOUD_URL=your_ibm_cloud_endpoint
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=your_watsonx_endpoint
GRANITE_MODEL_ID=your_granite_model_id
```

Add optional third-party API keys only if you intend to use those
integrations, for example:

``` env
OPENWEATHER_API_KEY=your_openweathermap_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

**Never commit `.env` or real credentials to GitHub.** The repository's
`.gitignore` should exclude `.env` files. Keep `.env.example` limited to
variable names and placeholder values.

### 5. Run the application

Use the entry point and run command defined by the project. For the
Flask application, the usual command is:

``` bash
python app.py
```

Then open the local address printed in the terminal (commonly
`http://127.0.0.1:5000`) in your browser.

> If the application uses a different startup command or port in your
> current version, follow the configuration in `app.py` and `README`/run
> instructions supplied with that version.

## 🔐 Security Notes

-   Keep API keys, IBM Cloud credentials, project IDs where treated as
    secrets, database credentials, and Flask secret keys out of source
    control.
-   Do not upload screenshots that show `.env` values, access tokens,
    private endpoints, or account details.
-   If a credential has been exposed, revoke or rotate it in the
    provider dashboard and update your local `.env`.
-   Use `.env.example` only for placeholder values.

## 🚀 Future Enhancements

Potential improvements include:

-   Interactive map-based itinerary visualization.
-   More detailed live transport and accommodation comparisons.
-   Booking-provider integrations and booking-status notifications.
-   Calendar export and schedule optimization.
-   User preference profiles and saved trips.
-   More robust validation and source links for visa, safety, and local
    travel guidance.
-   Automated tests and deployment configuration.

## 🎓 Project Information

  ----------------------------------------------------------------------------------------------------------------------------------------
  Detail                              Information
  ----------------------------------- ----------------------------------------------------------------------------------------------------
  Project title                       Travel Planner Agent

  Problem statement                   No. 5 -- Travel Planner Agent

  Program                             AICTE Edunet Foundation Project

  Mandatory technology                IBM Cloud Lite services / IBM Granite

  AI platform                         IBM watsonx.ai

  Repository                          [GitHub -- Travel Planner
                                      Agent](https://github.com/singhsovesh/Travel-Planner-Agent-Using-IBM-BOB-AICTE-Internship-Project)
  ----------------------------------------------------------------------------------------------------------------------------------------

## 👨‍💻 Author

**Sovesh Singh**

-   GitHub: [@singhsovesh](https://github.com/singhsovesh)
-   Project repository: [Travel Planner
    Agent](https://github.com/singhsovesh/Travel-Planner-Agent-Using-IBM-BOB-AICTE-Internship-Project)

------------------------------------------------------------------------

::: {align="center"}
**Built with Python and IBM Granite · AICTE Edunet Foundation Project**
:::
