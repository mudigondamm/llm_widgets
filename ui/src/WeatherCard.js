import React from 'react';

function WeatherCard({ city, data, isEditing, setCity, setIsEditing, handleBlur, handleKeyDown, fetchWeather }) {
  return (
    <div className="tile blue">
      <h3>Weather</h3>
      <div className="editable-field" onClick={() => setIsEditing(true)}>
        {isEditing ? (
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            onBlur={() => handleBlur(setIsEditing, fetchWeather, city)}
            onKeyDown={(e) => handleKeyDown(e, setIsEditing, fetchWeather, city)}
            autoFocus
          />
        ) : (
          <span>{city}</span>
        )}
      </div>
      <div className="info">
        {data ? (
          data.error ? (
            <p className="error">{data.error}</p>
          ) : (
            <>
              <p className="temp">{data.temperature}°C</p>
              <p className="description">{data.description}</p>
            </>
          )
        ) : (
          <p>Loading weather...</p>
        )}
      </div>
    </div>
  );
}

export default WeatherCard;