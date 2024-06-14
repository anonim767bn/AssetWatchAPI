import React from 'react';
import { Card, Typography } from 'antd';

const { Text } = Typography;

function CryptocurrencyCard(props) {
  const { currency } = props;

  return (
    <div>
      <Card
        title={
          <div className="flex items-center gap-4">
            <img src={`https://s2.coinmarketcap.com/static/img/coins/64x64/${currency.imageId}.png`}/>
            <span style={{ fontSize: '2em' }}>{currency.name}</span>
          </div>
        }
        style={{ 
          width: 500, 
          marginBottom: 20, 
          border: '2px solid #000', // Увеличиваем толщину границы
          boxShadow: '5px 5px 15px rgba(0, 0, 0, 0.15)' // Добавляем тень
        }}
      >
        <p><Text strong style={{ fontSize: '1.5em' }}>Текущая цена:</Text> <Text style={{ fontSize: '2em', color: '#00ff00' }}>${parseFloat(currency.price).toFixed(3)}</Text></p>
        <p><Text strong style={{ fontSize: '1.5em' }}>Обновлено:</Text> <Text style={{ fontSize: '2em' }}>{new Date(currency.sync_timestamp).toLocaleString()}</Text></p>
      </Card>
    </div>
  );
}

export default CryptocurrencyCard;