import { Request, Response } from 'express';
import feeService from '../services/feeService';

export const createFee = async (req: Request, res: Response) => {
  try {
    const { caseId, amount, description, type, dueDate } = req.body;
    const tenantId = req.user?.tenantId;
    const createdBy = req.user?.id;

    if (!tenantId || !createdBy) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const fee = await feeService.createFee({
      caseId,
      amount,
      description,
      type,
      dueDate: new Date(dueDate),
      tenantId,
      createdBy,
    });

    res.status(201).json(fee);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create fee' });
  }
};

export const getFee = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const fee = await feeService.getFee(id, tenantId);
    if (!fee) {
      return res.status(404).json({ error: 'Fee not found' });
    }

    res.json(fee);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get fee' });
  }
};

export const listFees = async (req: Request, res: Response) => {
  try {
    const { caseId } = req.query;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const fees = await feeService.listFees(tenantId, caseId as string | undefined);
    res.json(fees);
  } catch (error) {
    res.status(500).json({ error: 'Failed to list fees' });
  }
};

export const updateFeeStatus = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { status, paidDate } = req.body;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const fee = await feeService.updateFeeStatus(
      id,
      tenantId,
      status,
      paidDate ? new Date(paidDate) : undefined
    );

    res.json(fee);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update fee status' });
  }
};

export const createCommission = async (req: Request, res: Response) => {
  try {
    const { feeId, userId, percentage } = req.body;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const commission = await feeService.createCommission({
      feeId,
      userId,
      percentage,
      tenantId,
    });

    res.status(201).json(commission);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create commission' });
  }
};

export const updateCommissionStatus = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { status, paidDate } = req.body;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const commission = await feeService.updateCommissionStatus(
      id,
      tenantId,
      status,
      paidDate ? new Date(paidDate) : undefined
    );

    res.json(commission);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update commission status' });
  }
};

export const getCommissionsByUser = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const commissions = await feeService.getCommissionsByUser(userId, tenantId);
    res.json(commissions);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get user commissions' });
  }
};

export const getCommissionsByFee = async (req: Request, res: Response) => {
  try {
    const { feeId } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const commissions = await feeService.getCommissionsByFee(feeId, tenantId);
    res.json(commissions);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get fee commissions' });
  }
}; 