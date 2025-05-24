import React, { useState, useEffect } from 'react';

function ProductForm({ productToEdit, onSave, onCancel }) {
  const [nombre, setNombre] = useState('');
  const [precio, setPrecio] = useState('');
  const [imagen, setImagen] = useState('');

  useEffect(() => {
    // Si hay un producto para editar, carga sus datos en el formulario
    if (productToEdit) {
      setNombre(productToEdit.nombre);
      setPrecio(productToEdit.precio);
      setImagen(productToEdit.imagen);
    } else {
      // Si no, limpia el formulario
      setNombre('');
      setPrecio('');
      setImagen('');
    }
  }, [productToEdit]); // Se ejecuta cada vez que productToEdit cambia

  const handleSubmit = (e) => {
    e.preventDefault();
    const product = {
      id: productToEdit ? productToEdit.id : null, // Mantén el ID si editas
      nombre,
      precio: parseFloat(precio), // Convierte el precio a número
      imagen,
    };
    onSave(product);
  };

  return (
    <div>
      <h2>{productToEdit ? 'Editar Producto' : 'Agregar Nuevo Producto'}</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="nombre">Nombre:</label>
          <input
            type="text"
            id="nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="precio">Precio:</label>
          <input
            type="number"
            id="precio"
            value={precio}
            onChange={(e) => setPrecio(e.target.value)}
            required
            step="0.01"
          />
        </div>
        <div>
          <label htmlFor="imagen">URL/Ruta de Imagen:</label>
          <input
            type="text"
            id="imagen"
            value={imagen}
            onChange={(e) => setImagen(e.target.value)}
          />
        </div>
        <button type="submit">Guardar</button>
        <button type="button" onClick={onCancel}>Cancelar</button>
      </form>
    </div>
  );
}

export default ProductForm;
