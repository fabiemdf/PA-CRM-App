import express from 'express';
import { PrismaClient } from '@prisma/client';

const router = express.Router();
const prisma = new PrismaClient();

// Create a new tenant
router.post('/', async (req, res) => {
  try {
    const { name } = req.body;
    const tenant = await prisma.tenant.create({
      data: {
        name,
      },
    });
    res.json(tenant);
  } catch (error) {
    console.error('Error creating tenant:', error);
    res.status(500).json({ error: 'Failed to create tenant' });
  }
});

// Get all tenants
router.get('/', async (_req, res) => {
  try {
    const tenants = await prisma.tenant.findMany();
    res.json(tenants);
  } catch (error) {
    console.error('Error fetching tenants:', error);
    res.status(500).json({ error: 'Failed to fetch tenants' });
  }
});

export default router; 