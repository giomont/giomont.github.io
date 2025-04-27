# Product Inventory App

This project is a web application for managing product information, including name, price, and quantity. It consists of a frontend built with Angular and a backend using Node.js and Express, with data stored in a free online database.

## Project Structure

```
product-inventory-app
├── frontend
│   ├── src
│   │   ├── app
│   │   │   ├── components
│   │   │   │   ├── product-list
│   │   │   │   ├── product-form
│   │   │   │   └── product-detail
│   │   │   ├── services
│   │   │   │   └── product.service.ts
│   │   │   ├── models
│   │   │   │   └── product.ts
│   │   │   └── app.component.ts
│   │   ├── assets
│   │   └── index.html
│   ├── package.json
│   └── tsconfig.json
├── backend
│   ├── src
│   │   ├── controllers
│   │   │   └── product.controller.ts
│   │   ├── models
│   │   │   └── product.model.ts
│   │   ├── routes
│   │   │   └── product.routes.ts
│   │   └── app.ts
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Features

- Add, edit, and delete products.
- View a list of all products.
- View detailed information about each product.

## Getting Started

### Prerequisites

- Node.js
- Angular CLI

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the frontend directory and install dependencies:
   ```
   cd frontend
   npm install
   ```

3. Navigate to the backend directory and install dependencies:
   ```
   cd backend
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```
   cd backend
   npm start
   ```

2. In a new terminal, start the frontend application:
   ```
   cd frontend
   ng serve
   ```

3. Open your browser and navigate to `http://localhost:4200` to view the application.

## Contributing

Feel free to submit issues or pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License.