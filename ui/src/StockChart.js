import React from 'react';

function StockChart({ ticker, data, isEditing, setTicker, setIsEditing, handleBlur, handleKeyDown, fetchStock }) {
  return (
    <div className="tile green">
      <h3>Stock Price</h3>
      <div className="editable-field" onClick={() => setIsEditing(true)}>
        {isEditing ? (
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            onBlur={() => handleBlur(setIsEditing, fetchStock, ticker)}
            onKeyDown={(e) => handleKeyDown(e, setIsEditing, fetchStock, ticker)}
            autoFocus
          />
        ) : (
          <span>{ticker}</span>
        )}
      </div>
      <div className="info">
        {data ? (
          data.error ? (
            <p className="error">{data.error}</p>
          ) : (
            <>
              <p className="price">{data.price} {data.currency}</p>
              <p className="change">{data.change}</p>
            </>
          )
        ) : (
          <p>Loading stock...</p>
        )}
      </div>
    </div>
  );
}

export default StockChart;