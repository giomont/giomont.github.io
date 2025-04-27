import { Injectable } from '@nestjs/common';
import { MongoClient } from 'mongodb';
import { Product } from '../models/product.model';

@Injectable()
export class DatabaseService {
    private client: MongoClient;
    private dbName: string = 'your_database_name'; // Replace with your database name
    private collectionName: string = 'products'; // Collection for products

    constructor() {
        this.connect();
    }

    private async connect() {
        const uri = 'your_mongodb_connection_string'; // Replace with your MongoDB connection string
        this.client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });
        await this.client.connect();
    }

    public async addProduct(product: Product): Promise<void> {
        const db = this.client.db(this.dbName);
        await db.collection(this.collectionName).insertOne(product);
    }

    public async getProducts(): Promise<Product[]> {
        const db = this.client.db(this.dbName);
        return await db.collection(this.collectionName).find().toArray();
    }

    public async updateProduct(id: string, product: Product): Promise<void> {
        const db = this.client.db(this.dbName);
        await db.collection(this.collectionName).updateOne({ _id: new ObjectId(id) }, { $set: product });
    }

    public async deleteProduct(id: string): Promise<void> {
        const db = this.client.db(this.dbName);
        await db.collection(this.collectionName).deleteOne({ _id: new ObjectId(id) });
    }

    public async closeConnection(): Promise<void> {
        await this.client.close();
    }
}