import React, { useEffect, useState } from 'react';
import { Menu, Spin } from 'antd';
import axios from 'axios';
import CryptocurrencyCard from './components/cryptocurrencyCard.jsx';

const App = () => {
  const [currencies, setCurrencies] = useState([]);
  const [currencyId, setCurrencyId] = useState(1);
  const [currencyData, setCurrencyData] = useState(null);

  const fetchCurrency = () => {
    axios.get('http://127.0.0.1:8000/cryptocurrencies').then((response) => {
      const currenciesResponse = response.data;
      const menuItems = [
        {
          key: 'g1',
          label: 'Список криптовалют',
          type: 'group',
          children: currenciesResponse.map((currency, index) => ({
            key: (index + 1).toString(),
            label: currency.name,
            imageId: index + 1, // Add this line
          })),
        },
      ];
      setCurrencies(menuItems);
    });
  };

  const fetchCurrencyId = () => {
    axios.get(`http://127.0.0.1:8000/cryptocurrencies/${currencyId}`).then((response) => {
      const currencyDataWithImageId = {
        ...response.data,
        imageId: currencyId, // Add this line
      };
      setCurrencyData(currencyDataWithImageId);
    });
  };

  useEffect(() => {
    fetchCurrency();
  }, []);

  useEffect(() => {
    setCurrencyData(null);
    fetchCurrencyId();
  }, [currencyId]);

  const onClick = (e) => {
    setCurrencyId(e.key);
  };

  return (
    <div className='flex '>
      <Menu
        onClick={onClick}
        style={{
          width: 256,
        }}
        defaultSelectedKeys={['1']}
        defaultOpenKeys={['g1']}
        mode="inline"
        items={currencies}
        className='h-screen overflow-scroll'
      />
      <div className='mx-auto my-auto'>
        {currencyData ? <CryptocurrencyCard currency={currencyData}/> : <Spin size="large"/>}
      </div>
    </div>
  );
};

export default App;