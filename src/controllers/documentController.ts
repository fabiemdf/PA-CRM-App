import { Request, Response } from 'express';
import documentService from '../services/documentService';
import multer from 'multer';
import { Readable } from 'stream';

// Configure multer for memory storage
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
});

export const uploadMiddleware = upload.single('file');

export const createDocument = async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { name, type, caseId } = req.body;
    const tenantId = req.user?.tenantId;
    const createdBy = req.user?.id;

    if (!tenantId || !createdBy) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const document = await documentService.createDocument(
      req.file.buffer,
      {
        name: name || req.file.originalname,
        type,
        mimeType: req.file.mimetype,
        size: req.file.size,
        caseId,
        tenantId,
        createdBy,
      },
      req.body.metadata ? JSON.parse(req.body.metadata) : undefined
    );

    res.status(201).json(document);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create document' });
  }
};

export const getDocument = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const document = await documentService.getDocument(id, tenantId);
    if (!document) {
      return res.status(404).json({ error: 'Document not found' });
    }

    res.json(document);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get document' });
  }
};

export const listDocuments = async (req: Request, res: Response) => {
  try {
    const { caseId } = req.query;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const documents = await documentService.listDocuments(tenantId, caseId as string | undefined);
    res.json(documents);
  } catch (error) {
    res.status(500).json({ error: 'Failed to list documents' });
  }
};

export const updateDocument = async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { id } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const document = await documentService.updateDocument(
      id,
      tenantId,
      req.file.buffer,
      req.body.metadata ? JSON.parse(req.body.metadata) : undefined
    );

    res.json(document);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update document' });
  }
};

export const searchDocuments = async (req: Request, res: Response) => {
  try {
    const { query } = req.query;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!query || typeof query !== 'string') {
      return res.status(400).json({ error: 'Search query is required' });
    }

    const documents = await documentService.searchDocuments(tenantId, query);
    res.json(documents);
  } catch (error) {
    res.status(500).json({ error: 'Failed to search documents' });
  }
};

export const getDocumentVersion = async (req: Request, res: Response) => {
  try {
    const { id, version } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const documentVersion = await documentService.getDocumentVersion(
      id,
      parseInt(version),
      tenantId
    );

    if (!documentVersion) {
      return res.status(404).json({ error: 'Document version not found' });
    }

    res.json(documentVersion);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get document version' });
  }
}; 