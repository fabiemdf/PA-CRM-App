import { Router } from 'express';
import {
  createDocument,
  getDocument,
  listDocuments,
  updateDocument,
  searchDocuments,
  getDocumentVersion,
  uploadMiddleware,
} from '../controllers/documentController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// All routes require authentication
router.use(authenticateToken);

// Document routes
router.post('/', uploadMiddleware, createDocument);
router.get('/', listDocuments);
router.get('/search', searchDocuments);
router.get('/:id', getDocument);
router.put('/:id', uploadMiddleware, updateDocument);
router.get('/:id/versions/:version', getDocumentVersion);

export default router; 