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

export const customerFormSchema = z.object({
  customer_number: z
    .string()
    .trim()
    .max(
      50,
      "Customer number is too long.",
    ),

  first_name: z
    .string()
    .trim()
    .min(1, "First name is required.")
    .max(100, "First name is too long."),

  last_name: z
    .string()
    .trim()
    .max(100, "Last name is too long."),

  other_names: z
    .string()
    .trim()
    .max(150, "Other names are too long."),

  phone: z
    .string()
    .trim()
    .max(50, "Phone is too long."),

  email: optionalEmail,

  gender: z
    .string()
    .trim()
    .max(20, "Gender is too long."),

  date_of_birth: z.string().trim(),

  id_number: z
    .string()
    .trim()
    .max(50, "ID number is too long."),

  address: z.string().trim(),

  city: z
    .string()
    .trim()
    .max(100, "City is too long."),
});

export type CustomerFormValues = z.infer<
  typeof customerFormSchema
>;
