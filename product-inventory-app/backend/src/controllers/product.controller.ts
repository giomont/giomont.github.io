export class ProductController {
    private products: any[] = [];

    public createProduct(req: any, res: any) {
        const { name, price, quantity } = req.body;
        const newProduct = { id: this.products.length + 1, name, price, quantity };
        this.products.push(newProduct);
        res.status(201).json(newProduct);
    }

    public getProducts(req: any, res: any) {
        res.status(200).json(this.products);
    }

    public getProductById(req: any, res: any) {
        const productId = parseInt(req.params.id);
        const product = this.products.find(p => p.id === productId);
        if (product) {
            res.status(200).json(product);
        } else {
            res.status(404).json({ message: 'Product not found' });
        }
    }

    public updateProduct(req: any, res: any) {
        const productId = parseInt(req.params.id);
        const { name, price, quantity } = req.body;
        const productIndex = this.products.findIndex(p => p.id === productId);
        if (productIndex !== -1) {
            this.products[productIndex] = { id: productId, name, price, quantity };
            res.status(200).json(this.products[productIndex]);
        } else {
            res.status(404).json({ message: 'Product not found' });
        }
    }

    public deleteProduct(req: any, res: any) {
        const productId = parseInt(req.params.id);
        const productIndex = this.products.findIndex(p => p.id === productId);
        if (productIndex !== -1) {
            this.products.splice(productIndex, 1);
            res.status(204).send();
        } else {
            res.status(404).json({ message: 'Product not found' });
        }
    }
}