import React from 'react';
import { Provider } from 'react-redux';
import { store } from './store/store';
import LogInteraction from './components/LogInteraction';

function App() {
  return (
    <Provider store={store}>
      <LogInteraction />
    </Provider>
  );
}

export default App;