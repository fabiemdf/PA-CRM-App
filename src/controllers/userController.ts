import { Request, Response, NextFunction } from 'express';
import { UserService } from '../services/userService';
import { AppError } from '../utils/errorHandler';

export default {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await UserService.createUser(req.body);
      res.status(201).json({ user });
    } catch (err) {
      next(err);
    }
  },

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await UserService.login(req.body);
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  },

  async getProfile(req: Request, res: Response, next: NextFunction) {
    try {
      // Assume req.user is set by auth middleware
      const userId = req.user?.userId;
      if (!userId) throw new AppError('User not authenticated', 401);
      const user = await UserService.getUserProfile(userId);
      res.status(200).json({ user });
    } catch (err) {
      next(err);
    }
  },

  async updateProfile(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user?.userId;
      if (!userId) throw new AppError('User not authenticated', 401);
      const user = await UserService.updateUserProfile(userId, req.body);
      res.status(200).json({ user });
    } catch (err) {
      next(err);
    }
  },

  async listUsers(req: Request, res: Response, next: NextFunction) {
    try {
      // Role check should be handled by middleware
      const tenantId = req.user?.tenantId;
      if (!tenantId) throw new AppError('Tenant ID is required', 400);
      const users = await UserService.listUsers(tenantId);
      res.status(200).json({ users });
    } catch (err) {
      next(err);
    }
  },

  async changeUserRole(req: Request, res: Response, next: NextFunction) {
    try {
      // Role check should be handled by middleware
      const { userId, role } = req.body;
      const user = await UserService.changeUserRole(userId, role);
      res.status(200).json({ user });
    } catch (err) {
      next(err);
    }
  },

  async deleteUser(req: Request, res: Response, next: NextFunction) {
    try {
      // Role check should be handled by middleware
      const { userId } = req.params;
      await UserService.deleteUser(userId);
      res.status(204).send();
    } catch (err) {
      next(err);
    }
  }
}; 