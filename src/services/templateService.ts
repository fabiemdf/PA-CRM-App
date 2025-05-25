import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

interface CreateTemplateData {
  name: string;
  description?: string;
  content: string;
  category: string;
  variables?: string;
  tenantId: string;
  createdBy: string;
}

interface UpdateTemplateData {
  name?: string;
  description?: string;
  content?: string;
  category?: string;
  variables?: string;
}

class TemplateService {
  async createTemplate(data: CreateTemplateData) {
    return prisma.template.create({
      data,
    });
  }

  async getTemplate(id: string, tenantId: string) {
    return prisma.template.findFirst({
      where: {
        id,
        tenantId,
      },
    });
  }

  async listTemplates(tenantId: string, category?: string) {
    return prisma.template.findMany({
      where: {
        tenantId,
        ...(category ? { category } : {}),
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async updateTemplate(id: string, tenantId: string, data: UpdateTemplateData) {
    return prisma.template.update({
      where: {
        id,
      },
      data,
    });
  }

  async deleteTemplate(id: string, tenantId: string) {
    return prisma.template.delete({
      where: {
        id,
      },
    });
  }
}

export default new TemplateService(); 