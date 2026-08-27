import { z } from "zod";

const optionalEmail = z
  .string()
  .trim()
  .refine(
    (value) =>
      value.length === 0 ||
      z.email().safeParse(value).success,
    "Enter a valid email address.",
  );

const nonNegativeIntegerInput = z
  .string()
  .trim()
  .refine(
    (value) => {
      if (value.length === 0) {
        return true;
      }

      const parsed = Number(value);

      return (
        Number.isInteger(parsed) &&
        parsed >= 0
      );
    },
    "Enter a whole number of days.",
  );

const nonNegativeMoneyInput = z
  .string()
  .trim()
  .refine(
    (value) => {
      if (value.length === 0) {
        return true;
      }

      const parsed = Number(value);

      return (
        Number.isFinite(parsed) &&
        parsed >= 0
      );
    },
    "Enter a non-negative amount.",
  );

export const supplierFormSchema = z.object({
  supplier_code: z
    .string()
    .trim()
    .max(50, "Supplier code is too long."),

  name: z
    .string()
    .trim()
    .min(1, "Supplier name is required.")
    .max(200, "Supplier name is too long."),

  legal_name: z.string().trim(),
  contact_person: z.string().trim(),
  email: optionalEmail,
  phone: z.string().trim(),
  alternate_phone: z.string().trim(),
  address_line_1: z.string().trim(),
  address_line_2: z.string().trim(),
  city: z.string().trim(),
  county_or_region: z.string().trim(),
  country: z.string().trim(),
  postal_code: z.string().trim(),
  tax_number: z.string().trim(),
  registration_number: z.string().trim(),
  payment_terms_days: nonNegativeIntegerInput,
  credit_limit: nonNegativeMoneyInput,
  currency: z
    .string()
    .trim()
    .max(3, "Currency must use a 3-letter code."),
  notes: z.string().trim(),
});

export type SupplierFormValues = z.infer<
  typeof supplierFormSchema
>;
