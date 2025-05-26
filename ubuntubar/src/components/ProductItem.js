import React from 'react';

function ProductItem({ product, onEdit, onDelete }) {
  return (
    <li style={{ 
      border: '1px solid #ddd',
      padding: '15px',
      marginBottom: '15px',
      borderRadius: '8px',
      backgroundColor: '#fff',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h3 style={{ margin: '0 0 10px 0' }}>{product.nombre}</h3>
      <p style={{ margin: '5px 0', color: '#007bff' }}>Precio: ${product.precio.toFixed(2)}</p>
      {product.imagen && (
        <img 
          src={product.imagen} 
          alt={product.nombre} 
          style={{ 
            width: '100px', 
            height: 'auto',
            marginBottom: '10px',
            borderRadius: '4px'
          }} 
        />
      )}
      <div style={{ 
        display: 'flex', 
        gap: '10px',
        marginTop: '10px'
      }}>
        <button 
          onClick={() => onEdit(product)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Editar
        </button>
        <button 
          onClick={() => onDelete(product.id)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Eliminar
        </button>
      </div>
    </li>
  );
}

export default ProductItem;
