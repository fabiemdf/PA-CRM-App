// Add additional fields
export interface User {
  id: string;
  email: string;
  password: string;
  tenantId: string;
  firstName: string; // New field
  lastName: string;  // New field
  role: string;      // New field
  createdAt: Date;   // New field
  updatedAt: Date;   // New field
}

// Validation function
export const validateUser = (user: User): string[] => {
  const errors: string[] = [];
  if (!user.email) errors.push('Email is required');
  if (!user.password) errors.push('Password is required');
  if (!user.tenantId) errors.push('Tenant ID is required');
  if (!user.firstName) errors.push('First name is required');
  if (!user.lastName) errors.push('Last name is required');
  if (!user.role) errors.push('Role is required');
  return errors;
}; 