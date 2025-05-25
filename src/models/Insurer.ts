// Insurer model
export interface Insurer {
  id: string;
  name: string;
  email: string;
  phone: string;
  tenantId: string; // Reference to the tenant
  createdAt: Date;
  updatedAt: Date;
}

// Validation function
export const validateInsurer = (insurer: Insurer): string[] => {
  const errors: string[] = [];
  if (!insurer.name) errors.push('Name is required');
  if (!insurer.email) errors.push('Email is required');
  if (!insurer.phone) errors.push('Phone is required');
  if (!insurer.tenantId) errors.push('Tenant ID is required');
  return errors;
}; 