// Contact model
export interface Contact {
  id: string;
  name: string;
  email: string;
  phone: string;
  tenantId: string; // Reference to the tenant
  createdAt: Date;
  updatedAt: Date;
}

// Validation function
export const validateContact = (contact: Contact): string[] => {
  const errors: string[] = [];
  if (!contact.name) errors.push('Name is required');
  if (!contact.email) errors.push('Email is required');
  if (!contact.phone) errors.push('Phone is required');
  if (!contact.tenantId) errors.push('Tenant ID is required');
  return errors;
}; 