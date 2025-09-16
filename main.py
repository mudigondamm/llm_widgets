import os
import json
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from typing import Literal
from dotenv import load_dotenv
import requests

# Load environment variables from a .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Streaming Gemini Tool-Calling API",
    description="A backend for a streaming chat app with Gemini and tool-calling.",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client with API key
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# API keys for external services
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

# --- REAL API CALL FUNCTIONS ---

def get_current_weather(city: str) -> dict:
    """Get the current weather for a specific city using OpenWeatherMap."""
    print("key", OPENWEATHERMAP_API_KEY)
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "city": city,
            "temperature": data['main']['temp'],
            "unit": "Celsius",
            "description": data['weather'][0]['description']
        }
    else:
        return {"error": f"Failed to get weather for {city}. Status code: {response.status_code}"}

def get_stock_price2(ticker: str) -> dict:
    """Get the current stock price for a given ticker using Alpha Vantage."""
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": ALPHAVANTAGE_API_KEY,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'Global Quote' in data:
            quote = data['Global Quote']
            return {
                "ticker": quote['01. symbol'],
                "price": quote['05. price'],
                "change": quote['09. change'],
            }
        else:
            return {"error": "Invalid ticker or API limit reached."}
    else:
        return {"error": f"Failed to get stock price for {ticker}. Status code: {response.status_code}"}

def get_pokemon_info(name: str) -> dict:
    """Get information about a Pokémon character using PokeAPI."""
    base_url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        types = [t['type']['name'] for t in data['types']]
        abilities = [a['ability']['name'] for a in data['abilities']]
        return {
            "name": data['name'].capitalize(),
            "type": ", ".join(types),
            "abilities": abilities,
            "image": data['sprites']['front_default']
        }
    else:
        return {"error": f"Failed to get info for {name}. Status code: {response.status_code}"}



# Mock tool functions (same as before)
def get_current_weather1(city: str) -> dict:
    weather_info = {
        "San Francisco": {"temperature": 15, "unit": "Celsius", "description": "Cloudy"},
        "New York": {"temperature": 22, "unit": "Celsius", "description": "Sunny"},
        "Atlanta": {"temperature": 25, "unit": "Celsius", "description": "Partly cloudy"},
    }
    return weather_info.get(city, {"error": "City not found"})


def get_stock_price(ticker: str) -> dict:
    stock_info = {
        "AAPL": {"price": 175.24, "currency": "USD", "change": "+1.2%"},
        "GOOG": {"price": 135.89, "currency": "USD", "change": "-0.5%"},
    }
    return stock_info.get(ticker.upper(), {"error": "Ticker not found"})


def get_pokemon_info1(name: str) -> dict:
    pokemon_info = {
        "Pikachu": {"type": "Electric", "abilities": ["Static"], "image": "URL_to_Pikachu_image"},
    }
    return pokemon_info.get(name.capitalize(), {"error": "Pokémon not found"})


# Function map to call the right tool
tools_map = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
    "get_pokemon_info": get_pokemon_info,
}


# The streaming chat endpoint with tool calls and a system prompt
@app.post("/stream_chat")
async def stream_chat(message: str):
    # Set up the chat with the system prompt and tools
    model = genai.GenerativeModel(
        "gemini-1.5-pro-latest",
        system_instruction="You are a helpful assistant that will update widget data using answer natural language queries.",
        tools=[
            {
                "function_declarations": [
                    {
                        "name": "get_current_weather",
                        "description": "Get the current weather for a specific city.",
                        "parameters": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                        },
                    },
                    {
                        "name": "get_stock_price",
                        "description": "Get the current stock price for a given ticker.",
                        "parameters": {
                            "type": "object",
                            "properties": {"ticker": {"type": "string"}},
                        },
                    },
                    {
                        "name": "get_pokemon_info",
                        "description": "Get information about a Pokémon character.",
                        "parameters": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        },
                    },
                ]
            }
        ],
    )
    chat = model.start_chat()

    async def event_generator():
        try:
            response_stream = chat.send_message(message, stream=True)

            # Use a standard 'for' loop to iterate over the synchronous iterator
            for chunk in response_stream:
                if hasattr(chunk.candidates[0].content.parts[0], 'function_call'):
                    tool_calls = chunk.candidates[0].content.parts
                    tool_outputs = []

                    for tool_call_part in tool_calls:
                        tool_call = tool_call_part.function_call
                        function_name = tool_call.name

                        function_args = dict(tool_call.args)

                        if function_name in tools_map:
                            function_output = tools_map[function_name](**function_args)
                            tool_outputs.append({
                                "name": function_name,
                                "response": function_output
                            })

                            # Stream an immediate widget update to the frontend
                            if function_name == "get_current_weather":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'weather', 'data': {'city': function_args.get('city'), 'info': function_output}})}\n\n"
                            elif function_name == "get_stock_price":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'stock', 'data': {'ticker': function_args.get('ticker'), 'info': function_output}})}\n\n"
                            elif function_name == "get_pokemon_info":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'pokemon', 'data': {'name': function_args.get('name'), 'info': function_output}})}\n\n"

                    # Send all tool outputs back to the model for a final response
                    tool_response_parts = [
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=output['name'],
                                response=output['response']
                            )
                        ) for output in tool_outputs
                    ]

                    final_response_stream = chat.send_message(tool_response_parts, stream=True)

                    # Stream the final, human-readable response to the client
                    for final_chunk in final_response_stream:
                        final_text = final_chunk.text
                        if final_text:
                            yield f"data: {json.dumps({'type': 'text', 'text': final_text})}\n\n"
                    return

                # If no tool call, stream the text content directly
                text_content = chunk.text
                if text_content:
                    yield f"data: {json.dumps({'type': 'text', 'text': text_content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'text', 'text': 'Error: ' + str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Standard RESTful endpoints for the tiles (unchanged)
@app.get("/weather/{city}")
async def get_weather_data(city: str):
    return get_current_weather(city)


@app.get("/stocks/{ticker}")
async def get_stock_data(ticker: str):
    return get_stock_price(ticker)


@app.get("/pokemon/{name}")
async def get_pokemon_data(name: str):
    return get_pokemon_info(name)