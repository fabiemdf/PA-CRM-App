import { Router } from 'express';
import userController from '../controllers/userController';
import { authenticateToken, requireRole } from '../middleware/auth';
import express, { Request } from 'express';
import { PrismaClient } from '@prisma/client';

interface AuthRequest extends Request {
  user?: {
    userId: string;
    tenantId: string;
    role: string;
  };
}

const router = Router();
const prisma = new PrismaClient();

// Public routes
router.post('/register', userController.register);
router.post('/login', userController.login);

// Protected routes
router.get('/profile', authenticateToken, userController.getProfile);
router.put('/profile', authenticateToken, userController.updateProfile);

// Admin-only routes
router.get('/', authenticateToken, requireRole(['ADMIN']), userController.listUsers);
router.patch('/role', authenticateToken, requireRole(['ADMIN']), userController.changeUserRole);
router.delete('/:userId', authenticateToken, requireRole(['ADMIN']), userController.deleteUser);

// Get current user profile
router.get('/me', authenticateToken, async (req: AuthRequest, res) => {
  try {
    if (!req.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const userId = req.user.userId;
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        tenantId: true,
        createdAt: true,
        updatedAt: true
      }
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(user);
  } catch (error) {
    console.error('Error fetching user profile:', error);
    res.status(500).json({ error: 'Failed to fetch user profile' });
  }
});

export default router; 