import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import TreeContainer from './components/TreeContainer';
import PropertyPanel from './components/PropertyPanel';
import SettingsModal from './components/SettingsModal';
import LogWindow from './components/LogWindow';
import { WebSocketProgressBar } from './components/WebSocketProgressBar';
import { useSettingsStore, useAppStore } from './store';
import './index.css';

const App: React.FC = () => {
  const { isOpen } = useSettingsStore();
  const { selectedProposal } = useAppStore();
  const [isProgressMinimized, setIsProgressMinimized] = useState(false);

  return (
    <div className="app">
      <Header />
      <WebSocketProgressBar 
        isMinimized={isProgressMinimized}
        onToggleMinimize={() => setIsProgressMinimized(!isProgressMinimized)}
      />
      <div className="main-content">
        <Sidebar />
        <div className="content-area">
          <TreeContainer />
        </div>
      </div>
      {isOpen && <SettingsModal />}
      <LogWindow />
    </div>
  );
};

export default App; 