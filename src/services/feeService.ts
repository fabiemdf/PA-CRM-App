import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

interface CreateFeeData {
  caseId: string;
  amount: number;
  description: string;
  type: string;
  dueDate: Date;
  tenantId: string;
  createdBy: string;
}

interface CreateCommissionData {
  feeId: string;
  userId: string;
  percentage: number;
  tenantId: string;
}

class FeeService {
  async createFee(data: CreateFeeData) {
    return prisma.fee.create({
      data,
    });
  }

  async getFee(id: string, tenantId: string) {
    return prisma.fee.findFirst({
      where: {
        id,
        tenantId,
      },
      include: {
        commissions: {
          include: {
            user: {
              select: {
                id: true,
                name: true,
                email: true,
              },
            },
          },
        },
      },
    });
  }

  async listFees(tenantId: string, caseId?: string) {
    return prisma.fee.findMany({
      where: {
        tenantId,
        ...(caseId ? { caseId } : {}),
      },
      include: {
        commissions: {
          include: {
            user: {
              select: {
                id: true,
                name: true,
                email: true,
              },
            },
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async updateFeeStatus(id: string, tenantId: string, status: string, paidDate?: Date) {
    return prisma.fee.update({
      where: {
        id,
      },
      data: {
        status,
        ...(paidDate ? { paidDate } : {}),
      },
    });
  }

  async createCommission(data: CreateCommissionData) {
    const fee = await prisma.fee.findUnique({
      where: {
        id: data.feeId,
      },
    });

    if (!fee) {
      throw new Error('Fee not found');
    }

    const amount = (fee.amount * data.percentage) / 100;

    return prisma.commission.create({
      data: {
        ...data,
        amount,
      },
    });
  }

  async updateCommissionStatus(id: string, tenantId: string, status: string, paidDate?: Date) {
    return prisma.commission.update({
      where: {
        id,
      },
      data: {
        status,
        ...(paidDate ? { paidDate } : {}),
      },
    });
  }

  async getCommissionsByUser(userId: string, tenantId: string) {
    return prisma.commission.findMany({
      where: {
        userId,
        tenantId,
      },
      include: {
        fee: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async getCommissionsByFee(feeId: string, tenantId: string) {
    return prisma.commission.findMany({
      where: {
        feeId,
        tenantId,
      },
      include: {
        user: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    });
  }
}

export default new FeeService(); 