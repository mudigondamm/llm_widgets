
# Instructions to the run LLM powered Widget app. 

This is a guide for setting up, running, and interacting with the full-stack application we built.
The application consists of a React frontend and a FastAPI backend. Powered by Gemini LLM.

Mainly it consists of UI app built using React App and Backend api with restful endpoints
and stream_chat endpoint to stream the response back to the frontend.

## Running the Backend
The backend is built with FastAPI and Python 3.9+. It handles all API requests, including tool calls and the multi-agent system.

### Prerequisites
Python 3.9+ installed.

pip for package management.

API keys for Google Gemini, OpenWeatherMap, and Alpha Vantage.

### Setup
Clone the Repository (if applicable) or ensure all your backend files are in one directory.

Create a virtual environment to manage dependencies:

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install dependencies from the requirements.txt file:

Bash

pip install -r requirements.txt
Create a .env file in the same directory as main.py and add your API keys:

GOOGLE_API_KEY="your_gemini_api_key_here"
OPENWEATHERMAP_API_KEY="your_openweathermap_api_key_here"
ALPHAVANTAGE_API_KEY="your_alphavantage_api_key_here"
Run the FastAPI server:

Bash

uvicorn main:app --reload
This will start the backend at http://127.0.0.1:8000. You can view the API documentation at http://127.0.0.1:8000/docs.

## Running the Frontend
The frontend is a React application. It serves as the user interface for displaying widgets and interacting with the chat.

### Prerequisites
Node.js and npm installed.

### Setup
Ensure all your frontend files (App.js, Board.js, WeatherCard.js, etc.) are in the src/ directory.

Install dependencies in the root of your React project:

Bash

npm install
Start the development server:

Bash

npm start
This will launch the app in your browser at http://localhost:3000.

## 🧩 Key Components
App.js: The main component that manages all the state (for widgets and chat) and contains the fetch logic to communicate with the backend. It renders the <Board /> component and the chat interface.

Board.js: A container component that organizes and renders the individual widget cards. It receives all the necessary data and handler functions as props from App.js.

Widget Components (WeatherCard.js, StockChart.js, etc.): These are custom components for each widget. They are responsible for rendering their specific data and handling inline editing.

main.py: The FastAPI backend. It contains:

Tool-calling functions (get_current_weather, etc.) that make real API calls.

The /stream_chat endpoint, which is the heart of the app.

4. 💬 Interacting with the App

A. Widget Updates (Single-Tool Calls)
Via Inline Editing: Click on the city, stock ticker, or Pokémon name on a widget. An input box will appear. Type a new value and press Enter to update the card.

Via Natural Language: Use the chat window to ask a question that triggers a single tool call. For example, "What is the weather in Atlanta?" will automatically update the weather card.