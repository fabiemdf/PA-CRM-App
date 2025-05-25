# Enhanced Public Adjuster CRM System

A comprehensive, scalable CRM system designed specifically for public adjusters with multi-tenant architecture, industry-specific features, and robust offline capabilities.

## Features

- Multi-tenant architecture with row-level security
- Document management with OCR capabilities
- Insurance carrier integration
- Compliance tracking
- Fee calculation & commission tracking
- Template system
- Photo/Video documentation
- E-signature integration

## Tech Stack

- **Backend**: Node.js with Express
- **Database**: PostgreSQL with Prisma ORM
- **Cache**: Redis
- **File Storage**: AWS S3 (Digital Ocean Spaces)
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## Prerequisites

- Node.js 18 or later
- Docker and Docker Compose
- PostgreSQL 14 or later
- Redis 7 or later

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/pa-crm-app.git
   cd pa-crm-app
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your configuration.

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start the development environment:
   ```bash
   docker-compose up -d
   ```

5. Run database migrations:
   ```bash
   npx prisma migrate dev
   ```

6. Start the development server:
   ```bash
   npm run dev
   ```

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run tests
- `npm run lint` - Run linter

## Project Structure

```
.
├── src/                    # Source code
│   ├── controllers/       # Route controllers
│   ├── middleware/        # Custom middleware
│   ├── models/           # Data models
│   ├── routes/           # API routes
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── prisma/               # Database schema and migrations
├── tests/               # Test files
├── docker/              # Docker configuration
└── docs/               # Documentation
```

## API Documentation

API documentation is available at `/api-docs` when running the server.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 