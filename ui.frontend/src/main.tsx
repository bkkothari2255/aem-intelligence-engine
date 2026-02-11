import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { Provider, defaultTheme } from '@adobe/react-spectrum';

console.log('AEM Intelligence: Initializing Chat Interface...');
console.log('AEM Intelligence: Initializing Chat Interface...');

function mountChatInterface() {
  const rootElement = document.getElementById('chat-interface-root');

  if (rootElement) {
    if (rootElement.hasChildNodes()) {
      console.log('AEM Intelligence: Chat Interface already mounted.');
      return;
    }
    
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <Provider theme={defaultTheme} colorScheme="light">
          <App />
        </Provider>
      </React.StrictMode>,
    );
    console.log('AEM Intelligence: Chat Interface mounted successfully.');
  } else {
    console.log('AEM Intelligence: Waiting for root element...');
    // Retry logic for AEM editor which might inject HTML later
    setTimeout(mountChatInterface, 500);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountChatInterface);
} else {
  mountChatInterface();
}
