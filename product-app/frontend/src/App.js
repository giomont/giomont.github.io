import React, { useState, useEffect } from 'react';
import ProductList from './components/ProductList';

function App() {
    const [products, setProducts] = useState([]);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const response = await fetch('/api/products');
            const data = await response.json();
            setProducts(data);
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    };

    return (
        <div className="App">
            <h1>Product Management</h1>
            <ProductList products={products} />
        </div>
    );
}

export default App;