import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';
import winston from 'winston';
import userRoutes from './routes/userRoutes';
import tenantRoutes from './routes/tenantRoutes';
import templateRoutes from './routes/templateRoutes';
import feeRoutes from './routes/feeRoutes';
import documentRoutes from './routes/documentRoutes';
import { errorHandler } from './utils/errorHandler';
import path from 'path';

// Load environment variables
dotenv.config();

// Initialize Prisma client
const prisma = new PrismaClient();

// Initialize logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple(),
  }));
}

// Initialize Express app
const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Serve static files from uploads directory
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Routes
app.use('/api/users', userRoutes);
app.use('/api/tenants', tenantRoutes);
app.use('/api/templates', templateRoutes);
app.use('/api/fees', feeRoutes);
app.use('/api/documents', documentRoutes);

// Error handling middleware
app.use(errorHandler);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Start server with port fallback
const startServer = async (port: number) => {
  try {
    await new Promise((resolve, reject) => {
      const server = app.listen(port, () => {
        logger.info(`Server is running on port ${port}`);
        resolve(server);
      }).on('error', (err: NodeJS.ErrnoException) => {
        if (err.code === 'EADDRINUSE') {
          logger.warn(`Port ${port} is in use, trying ${port + 1}`);
          reject(err);
        } else {
          logger.error('Server error:', err);
          reject(err);
        }
      });
    });
  } catch (err) {
    if (port < 3010) { // Try up to port 3010
      await startServer(port + 1);
    } else {
      logger.error('Could not find an available port');
      process.exit(1);
    }
  }
};

// Start server
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
startServer(PORT);

// Handle graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received. Closing HTTP server and Prisma client...');
  await prisma.$disconnect();
  process.exit(0);
}); 