import React, { useState, useEffect } from 'react';
import './App.css';
import WeatherCard from './WeatherCard';
import StockChart from './StockChart';
import PikachuCard from './PikachuCard';

// Base URL for your FastAPI backend
const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  // State for chat interface
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  // State for Weather Widget
  const [weatherCity, setWeatherCity] = useState('San Francisco');
  const [weatherData, setWeatherData] = useState(null);
  const [isEditingWeather, setIsEditingWeather] = useState(false);

  // State for Stock Widget
  const [stockTicker, setStockTicker] = useState('AAPL');
  const [stockData, setStockData] = useState(null);
  const [isEditingStock, setIsEditingStock] = useState(false);

  // State for Pokemon Widget
  const [pokemonName, setPokemonName] = useState('Pikachu');
  const [pokemonData, setPokemonData] = useState(null);
  const [isEditingPokemon, setIsEditingPokemon] = useState(false);

  // --- Utility Functions for Widgets (Standard GET requests) ---
  const fetchWeatherData = async (city) => {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/${city}`);
      if (!response.ok) throw new Error('Failed to fetch weather data');
      const data = await response.json();
      setWeatherData(data);
    } catch (error) {
      console.error("Error fetching weather:", error);
      setWeatherData({ error: "Could not retrieve weather data." });
    }
  };

  const fetchStockData = async (ticker) => {
    try {
      const response = await fetch(`${API_BASE_URL}/stocks/${ticker}`);
      if (!response.ok) throw new Error('Failed to fetch stock data');
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error("Error fetching stock:", error);
      setStockData({ error: "Could not retrieve stock data." });
    }
  };

  const fetchPokemonData = async (name) => {
    try {
      const response = await fetch(`${API_BASE_URL}/pokemon/${name}`);
      if (!response.ok) throw new Error('Failed to fetch pokemon data');
      const data = await response.json();
      setPokemonData(data);
    } catch (error) {
      console.error("Error fetching Pokemon:", error);
      setPokemonData({ error: "Could not retrieve Pokemon data." });
    }
  };


  useEffect(() => {
    fetchWeatherData(weatherCity);
    fetchStockData(stockTicker);
    fetchPokemonData(pokemonName);
  }, []); // Run once on component mount

  // --- Handlers for inline editing ---
  const handleEditBlur = (setter, fetcher, value) => {
    setter(false);
    if (value.trim() !== '') {
      fetcher(value);
    }
  };

  const handleEditKeyDown = (e, setter, fetcher, value) => {
    if (e.key === 'Enter') {
      setter(false);
      if (value.trim() !== '') {
        fetcher(value);
      }
    }
  };

  // --- Streaming Chat Logic (using POST and ReadableStream) ---
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    const userMessage = chatInput.trim();
    if (userMessage === '') return;

    setChatMessages(prev => [{ text: userMessage, sender: 'user' }, ...prev]);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/stream_chat?message=${encodeURIComponent(userMessage)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botResponseAccumulator = '';

      setChatMessages(prev => [{ text: '', sender: 'bot' }, ...prev]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          setIsTyping(false);
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

        for (const line of lines) {
          try {
            const data = JSON.parse(line.substring(5));

            if (data.type === 'text') {
              botResponseAccumulator += data.text;
              setChatMessages(prev => {
                const updatedMessages = [...prev];
                updatedMessages[0].text = botResponseAccumulator;
                return updatedMessages;
              });
            } else if (data.type === 'widget_update') {
              if (data.widget === 'weather') {
                setWeatherData(data.data.info);
                setWeatherCity(data.data.city);
              } else if (data.widget === 'stock') {
                setStockData(data.data.info);
                setStockTicker(data.data.ticker);
              } else if (data.widget === 'pokemon') {
                setPokemonData(data.data.info);
                setPokemonName(data.data.name);
              }
            }

          } catch (jsonError) {
            console.error("Failed to parse JSON chunk:", line, jsonError);
          }
        }
      }
    } catch (error) {
      console.error('Streaming chat error:', error);
      setChatMessages(prev => [{ text: `Error: ${error.message}`, sender: 'bot' }, ...prev]);
      setIsTyping(false);
    } finally {
      setChatInput('');
    }
  };

  return (
    <div className="app-container">
      {/* Left Column: Widgets */}
      <div className="widgets-column">
        <WeatherCard
          city={weatherCity}
          data={weatherData}
          isEditing={isEditingWeather}
          setCity={setWeatherCity}
          setIsEditing={setIsEditingWeather}
          handleBlur={handleEditBlur}
          handleKeyDown={handleEditKeyDown}
          fetchWeather={fetchWeatherData}
        />
        <StockChart
          ticker={stockTicker}
          data={stockData}
          isEditing={isEditingStock}
          setTicker={setStockTicker}
          setIsEditing={setIsEditingStock}
          handleBlur={handleEditBlur}
          handleKeyDown={handleEditKeyDown}
          fetchStock={fetchStockData}
        />
        <PikachuCard
          name={pokemonName}
          data={pokemonData}
          isEditing={isEditingPokemon}
          setName={setPokemonName}
          setIsEditing={setIsEditingPokemon}
          handleBlur={handleEditBlur}
          handleKeyDown={handleEditKeyDown}
          fetchPokemon={fetchPokemonData}
        />
      </div>

      {/* Right Column: Chat Interface */}
      <div className="chat-column">
        <div className="chat-interface tile">
          <form onSubmit={handleChatSubmit} className="chat-input-form">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about weather, stocks, or Pokémon..."
              className="chat-input"
              disabled={isTyping}
            />
            <button type="submit" disabled={isTyping}>Send</button>
          </form>
          <div className="chat-messages">
            {chatMessages.map((message, index) => (
              <div key={index} className={`chat-message ${message.sender}`}>
                {message.text}
              </div>
            ))}
            {isTyping && <div className="chat-message bot typing-indicator">...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;