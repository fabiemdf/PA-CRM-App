// Claim model
export interface Claim {
  id: string;
  title: string;
  description: string;
  status: string; // e.g., 'open', 'closed', 'pending'
  tenantId: string; // Reference to the tenant
  userId: string;   // Reference to the user who created the claim
  createdAt: Date;
  updatedAt: Date;
}

// Validation function
export const validateClaim = (claim: Claim): string[] => {
  const errors: string[] = [];
  if (!claim.title) errors.push('Title is required');
  if (!claim.description) errors.push('Description is required');
  if (!claim.status) errors.push('Status is required');
  if (!claim.tenantId) errors.push('Tenant ID is required');
  if (!claim.userId) errors.push('User ID is required');
  return errors;
}; 