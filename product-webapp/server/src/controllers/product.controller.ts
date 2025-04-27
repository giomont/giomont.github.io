import { Request, Response } from 'express';
import Product from '../models/product.model';
import { DatabaseService } from '../services/database.service';

export class ProductController {
    private dbService: DatabaseService;

    constructor() {
        this.dbService = new DatabaseService();
    }

    public async createProduct(req: Request, res: Response): Promise<void> {
        try {
            const productData = req.body;
            const newProduct = await this.dbService.createProduct(productData);
            res.status(201).json(newProduct);
        } catch (error) {
            res.status(500).json({ message: 'Error creating product', error });
        }
    }

    public async getProducts(req: Request, res: Response): Promise<void> {
        try {
            const products = await this.dbService.getProducts();
            res.status(200).json(products);
        } catch (error) {
            res.status(500).json({ message: 'Error fetching products', error });
        }
    }

    public async updateProduct(req: Request, res: Response): Promise<void> {
        try {
            const { id } = req.params;
            const productData = req.body;
            const updatedProduct = await this.dbService.updateProduct(id, productData);
            res.status(200).json(updatedProduct);
        } catch (error) {
            res.status(500).json({ message: 'Error updating product', error });
        }
    }

    public async deleteProduct(req: Request, res: Response): Promise<void> {
        try {
            const { id } = req.params;
            await this.dbService.deleteProduct(id);
            res.status(204).send();
        } catch (error) {
            res.status(500).json({ message: 'Error deleting product', error });
        }
    }
}