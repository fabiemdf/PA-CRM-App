import { PrismaClient } from '@prisma/client';
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

const prisma = new PrismaClient();

// Initialize S3 client for Digital Ocean Spaces
const s3Client = new S3Client({
  endpoint: process.env.DO_SPACES_ENDPOINT,
  region: process.env.DO_SPACES_REGION || 'nyc3',
  credentials: {
    accessKeyId: process.env.DO_SPACES_KEY || '',
    secretAccessKey: process.env.DO_SPACES_SECRET || '',
  },
});

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, '../../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

interface CreateDocumentData {
  name: string;
  type: string;
  mimeType: string;
  size: number;
  caseId?: string;
  tenantId: string;
  createdBy: string;
  metadata?: string;
}

class DocumentService {
  private async uploadToSpaces(file: Buffer, filename: string, mimeType: string): Promise<string> {
    const command = new PutObjectCommand({
      Bucket: process.env.DO_SPACES_BUCKET,
      Key: filename,
      Body: file,
      ContentType: mimeType,
      ACL: 'public-read',
    });

    await s3Client.send(command);
    return `${process.env.DO_SPACES_CDN_URL}/${filename}`;
  }

  private async extractTextFromDocument(file: Buffer, mimeType: string): Promise<string> {
    // For testing, we'll just return a placeholder text
    // In production, you would integrate with a proper OCR service
    return "Sample extracted text from document";
  }

  async createDocument(
    file: Buffer,
    data: CreateDocumentData,
    metadata?: Record<string, any>
  ) {
    const filename = `${uuidv4()}-${data.name}`;
    const url = await this.uploadToSpaces(file, filename, data.mimeType);

    // Extract text using OCR if it's a supported document type
    let ocrText: string | undefined;
    if (['application/pdf', 'image/jpeg', 'image/png'].includes(data.mimeType)) {
      ocrText = await this.extractTextFromDocument(file, data.mimeType);
    }

    return prisma.document.create({
      data: {
        ...data,
        url,
        ocrText,
        metadata: metadata ? JSON.stringify(metadata) : undefined,
      },
    });
  }

  async getDocument(id: string, tenantId: string) {
    return prisma.document.findFirst({
      where: {
        id,
        tenantId,
      },
      include: {
        versions: {
          orderBy: {
            version: 'desc',
          },
        },
      },
    });
  }

  async listDocuments(tenantId: string, caseId?: string) {
    return prisma.document.findMany({
      where: {
        tenantId,
        ...(caseId ? { caseId } : {}),
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async updateDocument(
    id: string,
    tenantId: string,
    file: Buffer,
    metadata?: Record<string, any>
  ) {
    const document = await prisma.document.findFirst({
      where: {
        id,
        tenantId,
      },
    });

    if (!document) {
      throw new Error('Document not found');
    }

    const filename = `${uuidv4()}-${document.name}`;
    const url = await this.uploadToSpaces(file, filename, document.mimeType);

    // Extract text using OCR if it's a supported document type
    let ocrText: string | undefined;
    if (['application/pdf', 'image/jpeg', 'image/png'].includes(document.mimeType)) {
      ocrText = await this.extractTextFromDocument(file, document.mimeType);
    }

    // Create new version
    await prisma.documentVersion.create({
      data: {
        documentId: id,
        version: document.version + 1,
        url,
        ocrText,
        metadata: metadata ? JSON.stringify(metadata) : undefined,
        createdBy: document.createdBy,
      },
    });

    // Update document
    return prisma.document.update({
      where: {
        id,
      },
      data: {
        version: document.version + 1,
        url,
        ocrText,
        metadata: metadata ? JSON.stringify(metadata) : undefined,
      },
    });
  }

  async searchDocuments(tenantId: string, query: string) {
    return prisma.document.findMany({
      where: {
        tenantId,
        OR: [
          { name: { contains: query, mode: 'insensitive' } },
          { ocrText: { contains: query, mode: 'insensitive' } },
          { metadata: { contains: query, mode: 'insensitive' } },
        ],
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async getDocumentVersion(documentId: string, version: number, tenantId: string) {
    return prisma.documentVersion.findFirst({
      where: {
        documentId,
        version,
        document: {
          tenantId,
        },
      },
    });
  }
}

export default new DocumentService(); 