import { Request, Response } from 'express';
import templateService from '../services/templateService';

export const createTemplate = async (req: Request, res: Response) => {
  try {
    const { name, description, content, category, variables } = req.body;
    const tenantId = req.user?.tenantId;
    const createdBy = req.user?.id;

    if (!tenantId || !createdBy) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const template = await templateService.createTemplate({
      name,
      description,
      content,
      category,
      variables,
      tenantId,
      createdBy,
    });

    res.status(201).json(template);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create template' });
  }
};

export const getTemplate = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const template = await templateService.getTemplate(id, tenantId);
    if (!template) {
      return res.status(404).json({ error: 'Template not found' });
    }

    res.json(template);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get template' });
  }
};

export const listTemplates = async (req: Request, res: Response) => {
  try {
    const { category } = req.query;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const templates = await templateService.listTemplates(
      tenantId,
      category as string | undefined
    );

    res.json(templates);
  } catch (error) {
    res.status(500).json({ error: 'Failed to list templates' });
  }
};

export const updateTemplate = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { name, description, content, category, variables } = req.body;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const template = await templateService.updateTemplate(id, tenantId, {
      name,
      description,
      content,
      category,
      variables,
    });

    res.json(template);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update template' });
  }
};

export const deleteTemplate = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const tenantId = req.user?.tenantId;

    if (!tenantId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    await templateService.deleteTemplate(id, tenantId);
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete template' });
  }
}; 