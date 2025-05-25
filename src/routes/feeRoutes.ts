import { Router } from 'express';
import {
  createFee,
  getFee,
  listFees,
  updateFeeStatus,
  createCommission,
  updateCommissionStatus,
  getCommissionsByUser,
  getCommissionsByFee,
} from '../controllers/feeController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// All routes require authentication
router.use(authenticateToken);

// Fee routes
router.post('/', createFee);
router.get('/', listFees);
router.get('/:id', getFee);
router.patch('/:id/status', updateFeeStatus);

// Commission routes
router.post('/:feeId/commissions', createCommission);
router.patch('/commissions/:id/status', updateCommissionStatus);
router.get('/commissions/user/:userId', getCommissionsByUser);
router.get('/:feeId/commissions', getCommissionsByFee);

export default router; 