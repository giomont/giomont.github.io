# Product App

## Overview
This project is a web application that allows users to manage product information. It includes a backend built with Express and a frontend built with React. The application stores product details such as name, price, and quantity in a free online database.

## Project Structure
```
product-app
├── backend
│   ├── models
│   │   └── product.js
│   ├── routes
│   │   └── products.js
│   ├── app.js
│   └── package.json
├── frontend
│   ├── src
│   │   ├── components
│   │   │   └── ProductList.js
│   │   ├── App.js
│   │   └── index.js
│   ├── public
│   │   └── index.html
│   └── package.json
├── README.md
└── .gitignore
```

## Backend Setup
1. Navigate to the `backend` directory.
2. Install dependencies:
   ```
   npm install
   ```
3. Start the server:
   ```
   node app.js
   ```

## Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```
   npm install
   ```
3. Start the frontend application:
   ```
   npm start
   ```

## Usage
- The application allows users to create, read, update, and delete product information.
- Access the frontend application in your browser at `http://localhost:3000`.

## Technologies Used
- **Backend**: Node.js, Express, Mongoose
- **Frontend**: React

## License
This project is licensed under the MIT License.