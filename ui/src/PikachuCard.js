import React from 'react';

function PikachuCard({ name, data, isEditing, setName, setIsEditing, handleBlur, handleKeyDown, fetchPokemon }) {
  return (
    <div className="tile blue">
      <h3>Pokemon</h3>
      <div className="editable-field" onClick={() => setIsEditing(true)}>
        {isEditing ? (
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => handleBlur(setIsEditing, fetchPokemon, name)}
            onKeyDown={(e) => handleKeyDown(e, setIsEditing, fetchPokemon, name)}
            autoFocus
          />
        ) : (
          <span>{name}</span>
        )}
      </div>
      <div className="info pokemon-info">
        {data ? (
          data.error ? (
            <p className="error">{data.error}</p>
          ) : (
            <>
              <img src={data.image || "https://via.placeholder.com/80"} alt={name} className="pokemon-image" />
              <p className="pokemon-name">{name}</p>
              <p className="pokemon-type">Type: {data.type}</p>
            </>
          )
        ) : (
          <p>Loading Pokemon...</p>
        )}
      </div>
    </div>
  );
}

export default PikachuCard;