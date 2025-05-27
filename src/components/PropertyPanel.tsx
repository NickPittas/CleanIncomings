import React from 'react';
import { useAppStore } from '../store';

const PropertyPanel: React.FC = () => {
  const { selectedProposal } = useAppStore();

  return (
    <div className="property-panel">
      <h3>Properties</h3>
      {selectedProposal ? (
        <div>
          <p>Editing: {selectedProposal.sourcePath}</p>
          {/* Property editing form will be added */}
        </div>
      ) : (
        <p>Select an item to edit properties</p>
      )}
    </div>
  );
};

export default PropertyPanel; 