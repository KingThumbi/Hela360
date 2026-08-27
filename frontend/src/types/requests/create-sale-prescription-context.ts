export interface CreateSalePrescriptionContext {
  prescription_reference?: string;

  prescriber_name: string;

  prescriber_registration_number?: string;

  prescription_date?: string;

  notes?: string;
}
