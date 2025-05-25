import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import jwt, { SignOptions } from 'jsonwebtoken';
import { AppError } from '../utils/errorHandler';

const prisma = new PrismaClient();

export interface CreateUserData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  tenantId: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UpdateUserData {
  firstName?: string;
  lastName?: string;
  email?: string;
}

export class UserService {
  static async createUser(data: CreateUserData) {
    const existingUser = await prisma.user.findUnique({
      where: { email: data.email },
    });

    if (existingUser) {
      throw new AppError('User already exists', 400);
    }

    const hashedPassword = await bcrypt.hash(data.password, 10);

    const user = await prisma.user.create({
      data: {
        ...data,
        password: hashedPassword,
      },
    });

    const token = this.generateToken(user.id, user.tenantId);

    return {
      user: this.sanitizeUser(user),
      token,
    };
  }

  static async login(data: LoginData) {
    const user = await prisma.user.findUnique({
      where: { email: data.email },
    });

    if (!user) {
      throw new AppError('Invalid credentials', 401);
    }

    const validPassword = await bcrypt.compare(data.password, user.password);

    if (!validPassword) {
      throw new AppError('Invalid credentials', 401);
    }

    const token = this.generateToken(user.id, user.tenantId);

    return {
      user: this.sanitizeUser(user),
      token,
    };
  }

  static async getUserProfile(userId: string) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new AppError('User not found', 404);
    }

    return this.sanitizeUser(user);
  }

  static async updateUserProfile(userId: string, data: UpdateUserData) {
    const user = await prisma.user.update({
      where: { id: userId },
      data,
    });

    return this.sanitizeUser(user);
  }

  static async listUsers(tenantId: string) {
    const users = await prisma.user.findMany({
      where: { tenantId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      },
    });
    return users;
  }

  static async changeUserRole(userId: string, role: string) {
    const user = await prisma.user.update({
      where: { id: userId },
      data: { role },
    });
    return this.sanitizeUser(user);
  }

  static async deleteUser(userId: string) {
    await prisma.user.delete({
      where: { id: userId },
    });
  }

  private static generateToken(userId: string, tenantId: string) {
    const expiresIn = (process.env.JWT_EXPIRES_IN || '24h') as any;
    const options: SignOptions = { expiresIn };
    return jwt.sign(
      { userId, tenantId },
      process.env.JWT_SECRET || 'your-development-secret-key',
      options
    );
  }

  private static sanitizeUser(user: any) {
    const { password, ...sanitizedUser } = user;
    return sanitizedUser;
  }
} 