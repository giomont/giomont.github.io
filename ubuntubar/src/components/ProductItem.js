import React from 'react';

function ProductItem({ product, onEdit, onDelete }) {
  return (
    <li>
      <h3>{product.nombre}</h3>
      <p>Precio: ${product.precio.toFixed(2)}</p>
      {product.imagen && (
        <img src={product.imagen} alt={product.nombre} style={{ width: '100px', height: 'auto' }} />
      )}
      <button onClick={() => onEdit(product)}>Editar</button>
      <button onClick={() => onDelete(product.id)}>Eliminar</button>
    </li>
  );
}

export default ProductItem;
