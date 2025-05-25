// Add additional fields
export interface Tenant {
  id: string;
  name: string;
  domain: string; // New field
  createdAt: Date; // New field
  updatedAt: Date; // New field
}

// Validation function
export const validateTenant = (tenant: Tenant): string[] => {
  const errors: string[] = [];
  if (!tenant.name) errors.push('Name is required');
  if (!tenant.domain) errors.push('Domain is required');
  return errors;
}; 