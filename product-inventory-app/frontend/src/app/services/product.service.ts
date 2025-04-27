export class ProductService {
    private apiUrl = 'https://your-backend-api-url.com/api/products'; // Replace with your backend API URL

    constructor(private http: HttpClient) {}

    getProducts() {
        return this.http.get<Product[]>(this.apiUrl);
    }

    getProductById(id: string) {
        return this.http.get<Product>(`${this.apiUrl}/${id}`);
    }

    createProduct(product: Product) {
        return this.http.post<Product>(this.apiUrl, product);
    }

    updateProduct(id: string, product: Product) {
        return this.http.put<Product>(`${this.apiUrl}/${id}`, product);
    }

    deleteProduct(id: string) {
        return this.http.delete(`${this.apiUrl}/${id}`);
    }
}