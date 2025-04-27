# Product Web Application

This is a simple web application designed to manage product information. It allows users to store and retrieve product details, including name, price, and quantity. The application is built using Angular for the client-side and Node.js with Express for the server-side.

## Project Structure

The project is divided into two main parts:

1. **Client**: The front-end application built with Angular.
   - Located in the `client` directory.
   - Contains components, services, models, and routing for the application.

2. **Server**: The back-end application built with Node.js and Express.
   - Located in the `server` directory.
   - Contains controllers, models, routes, and services for handling database interactions.

## Features

- Add, update, and delete products.
- View a list of all products.
- Responsive design using Bootstrap.

## Technologies Used

- Angular
- Node.js
- Express
- MongoDB (or any other free online database)

## Getting Started

### Prerequisites

- Node.js and npm installed on your machine.
- Angular CLI installed globally.

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the client directory and install dependencies:
   ```
   cd product-webapp/client
   npm install
   ```

3. Navigate to the server directory and install dependencies:
   ```
   cd ../server
   npm install
   ```

### Running the Application

1. Start the server:
   ```
   cd server
   npm start
   ```

2. In a new terminal, start the client:
   ```
   cd client
   ng serve
   ```

3. Open your browser and navigate to `http://localhost:4200` to view the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.