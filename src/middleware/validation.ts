import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain } from 'express-validator';
import { AppError } from '../utils/errorHandler';

export const validate = (validations: ValidationChain[]) => {
  return async (req: Request, _res: Response, next: NextFunction) => {
    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);
    if (errors.isEmpty()) {
      return next();
    }

    throw new AppError('Validation failed', 400);
  };
};

export const userValidation = {
  register: [
    // Add validation rules here
  ],
  login: [
    // Add validation rules here
  ],
  updateProfile: [
    // Add validation rules here
  ],
}; 