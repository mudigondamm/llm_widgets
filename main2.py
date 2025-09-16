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
    title="Gemini Multi-Flow API",
    description="A backend that handles both direct widget updates and a multi-agent system.",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client and LangChain models
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# API keys for external services
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

# --- Initialize Agent Models ---
llm_agentA = genai.GenerativeModel(
    "gemini-1.5-pro-latest",
    system_instruction="You are a factual data analyst. Describe the provided data in a clear, concise, and professional manner. Do not add creative flair.",
)
llm_agentB = genai.GenerativeModel(
    "gemini-1.5-pro-latest",
    system_instruction="You are a witty, speculative, and humorous commentator. Take the factual analysis and add wildly imaginative commentary. Be entertaining.",
)


# --- REAL API CALL FUNCTIONS ---

def get_current_weather(city: str) -> dict:
    """Gets the current weather for a specific city.

    Args:
        city (str): The name of the city.

    Returns:
        A dictionary with weather information.
    """
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


def get_stock_price(ticker: str) -> dict:
    """Gets the current stock price for a given ticker.

    Args:
        ticker (str): The stock ticker (e.g., 'GOOG').

    Returns:
        A dictionary with stock price information.
    """
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
    """Gets information about a Pokémon character.

    Args:
        name (str): The name of the Pokémon (e.g., 'Pikachu').

    Returns:
        A dictionary with Pokémon information.
    """
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


tools = [get_current_weather, get_stock_price, get_pokemon_info]
tools_map = {tool.__name__: tool for tool in tools}


# The streaming chat endpoint
@app.post("/stream_chat")
async def stream_chat(message: str):
    llm = genai.GenerativeModel("gemini-1.5-pro-latest", tools=tools)

    async def event_generator():
        try:
            if "explain this" in message.lower() or "summarize the board" in message.lower():
                board_tools_message = "What's the stock price for GOOG and the weather in New York?"
                response = llm.generate_content(board_tools_message)

                tool_calls = []
                if response.candidates and hasattr(response.candidates[0].content, 'parts') and hasattr(
                        response.candidates[0].content.parts[0], 'function_call'):
                    for tool_call_part in response.candidates[0].content.parts:
                        tool_call = tool_call_part.function_call
                        function_args = dict(tool_call.args)
                        tool_calls.append({"name": tool_call.name, "args": function_args})

                outputs = []
                for tool_call in tool_calls:
                    function_name = tool_call["name"]
                    function_args = tool_call["args"]
                    tool_output = tools_map[function_name](**function_args)
                    outputs.append(f"Tool: {function_name} -> Output: {tool_output}")

                analyst_input = "\n".join(outputs)
                analyst_output = llm_agentA.generate_content(f"Data: {analyst_input}").text

                commentator_output = llm_agentB.generate_content(f"Factual analysis: {analyst_output}").text

                yield f"data: {json.dumps({'type': 'ui_update', 'agent': 'A', 'content': analyst_output})}\n\n"
                yield f"data: {json.dumps({'type': 'ui_update', 'agent': 'B', 'content': commentator_output})}\n\n"

            else:
                response_stream = llm.generate_content(message, stream=True)

                if not hasattr(response_stream, '__iter__'):
                    response_stream = [response_stream]

                for chunk in response_stream:
                    if hasattr(chunk.candidates[0].content, 'parts') and hasattr(chunk.candidates[0].content.parts[0],
                                                                                 'function_call'):
                        tool_call = chunk.candidates[0].content.parts[0].function_call
                        function_name = tool_call.name
                        function_args = dict(tool_call.args)

                        if function_name in tools_map:
                            function_output = tools_map[function_name](**function_args)

                            if function_name == "get_current_weather":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'weather', 'data': {'city': function_args.get('city'), 'info': function_output}})}\n\n"
                            elif function_name == "get_stock_price":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'stock', 'data': {'ticker': function_args.get('ticker'), 'info': function_output}})}\n\n"
                            elif function_name == "get_pokemon_info":
                                yield f"data: {json.dumps({'type': 'widget_update', 'widget': 'pokemon', 'data': {'name': function_args.get('name'), 'info': function_output}})}\n\n"

                            final_response_stream = llm.generate_content([
                                genai.protos.Part(text=message),
                                genai.protos.Part(function_call=tool_call),
                                genai.protos.Part(function_response=genai.protos.FunctionResponse(name=function_name,
                                                                                                  response=function_output))
                            ], stream=True)

                            for final_chunk in final_response_stream:
                                if final_chunk.text:
                                    yield f"data: {json.dumps({'type': 'text', 'text': final_chunk.text})}\n\n"

                    else:
                        text_content = chunk.text
                        if text_content:
                            yield f"data: {json.dumps({'type': 'text', 'text': text_content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'text', 'text': 'Error: ' + str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Standard RESTful endpoints (unchanged)
@app.get("/weather/{city}")
async def get_weather_data(city: str):
    return get_current_weather(city)


@app.get("/stocks/{ticker}")
async def get_stock_data(ticker: str):
    return get_stock_price(ticker)


@app.get("/pokemon/{name}")
async def get_pokemon_data(name: str):
    return get_pokemon_info(name)