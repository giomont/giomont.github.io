import React, { useState, useEffect } from 'react';
import ProductList from './components/ProductList';
import ProductForm from './components/ProductForm';
import './App.css'; // Opcional: si quieres agregar estilos

function App() {
  const [products, setProducts] = useState([]);
  const [editingProduct, setEditingProduct] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // URL del archivo JSON en GitHub (asegúrate de usar la URL raw)
  // Reemplaza 'giomont' y 'giomont.github.io' con tu usuario y nombre de repositorio si son diferentes
  const JSON_DATA_URL = 'https://raw.githubusercontent.com/giomont/giomont.github.io/main/ubuntubar/products.json';

  useEffect(() => {
    // Cargar productos al iniciar la aplicación
    fetch(JSON_DATA_URL)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => setProducts(data))
      .catch(error => console.error("Error cargando los productos:", error));
  }, []); // El array vacío asegura que esto solo se ejecute una vez al montar

  const handleAddProduct = () => {
    setEditingProduct(null); // Para asegurar que es un nuevo producto
    setShowForm(true);
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setShowForm(true);
  };

  const handleDeleteProduct = (productId) => {
    // Filtra la lista para remover el producto con el ID dado
    const updatedProducts = products.filter(product => product.id !== productId);
    setProducts(updatedProducts);
    // NOTA: Los cambios no se guardan permanentemente en GitHub con esta acción.
    // Deberás actualizar manualmente el archivo products.json en GitHub.
    alert("Producto eliminado (temporalmente). Recuerda actualizar products.json en GitHub.");
  };

  const handleSaveProduct = (product) => {
    if (product.id) {
      // Editar producto existente
      const updatedProducts = products.map(p =>
        p.id === product.id ? product : p
      );
      setProducts(updatedProducts);
    } else {
      // Agregar nuevo producto
      const newProduct = { ...product, id: Date.now() }; // Genera un ID simple
      setProducts([...products, newProduct]);
    }
    setShowForm(false);
    setEditingProduct(null);
    // NOTA: Los cambios no se guardan permanentemente en GitHub con esta acción.
    // Deberás actualizar manualmente el archivo products.json en GitHub.
    alert("Producto guardado (temporalmente). Recuerda actualizar products.json en GitHub.");
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingProduct(null);
  };

  return (
    <div className="App">
      <h1>Gestión de Productos</h1>

      {!showForm && (
        <>
          <button onClick={handleAddProduct}>Agregar Nuevo Producto</button>
          <ProductList
            products={products}
            onEdit={handleEditProduct}
            onDelete={handleDeleteProduct}
          />
        </>
      )}

      {showForm && (
        <ProductForm
          productToEdit={editingProduct}
          onSave={handleSaveProduct}
          onCancel={handleCancelForm}
        />
      )}

      {/* Opcional: Mostrar el JSON actual para facilitar la copia manual */}
      <h2>Datos Actuales (para copiar y pegar en GitHub)</h2>
      <pre>{JSON.stringify(products, null, 2)}</pre>
    </div>
  );
}

export default App;
