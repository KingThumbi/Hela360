import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import {
  useForm,
  useWatch,
} from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  COUNTRIES,
  CURRENCIES,
} from "@/constants/reference";
import type { Supplier } from "@/types/entities";
import type {
  CreateSupplierRequest,
  UpdateSupplierRequest,
} from "@/types/requests";
import {
  supplierFormSchema,
  type SupplierFormValues,
} from "@/validation/supplierSchema";

interface SupplierFormDialogProps {
  open: boolean;
  mode: "create" | "edit";
  supplier?: Supplier | null;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onOpenChange: (open: boolean) => void;
  onCreate: (payload: CreateSupplierRequest) => void;
  onUpdate: (
    supplierId: string,
    payload: UpdateSupplierRequest,
  ) => void;
}

const emptyValues: SupplierFormValues = {
  supplier_code: "",
  name: "",
  legal_name: "",
  contact_person: "",
  email: "",
  phone: "",
  alternate_phone: "",
  address_line_1: "",
  address_line_2: "",
  city: "",
  county_or_region: "",
  country: "KE",
  postal_code: "",
  tax_number: "",
  registration_number: "",
  payment_terms_days: "",
  credit_limit: "",
  currency: "KES",
  notes: "",
};

function textOrNull(value: string): string | null {
  const trimmed = value.trim();

  return trimmed.length > 0 ? trimmed : null;
}

function optionalNumber(
  value: string,
): number | undefined {
  const trimmed = value.trim();

  return trimmed.length > 0
    ? Number(trimmed)
    : undefined;
}

function supplierToValues(
  supplier?: Supplier | null,
): SupplierFormValues {
  if (!supplier) {
    return emptyValues;
  }

  return {
    supplier_code: supplier.supplier_code,
    name: supplier.name,
    legal_name: supplier.legal_name ?? "",
    contact_person: supplier.contact_person ?? "",
    email: supplier.email ?? "",
    phone: supplier.phone ?? "",
    alternate_phone: supplier.alternate_phone ?? "",
    address_line_1: supplier.address_line_1 ?? "",
    address_line_2: supplier.address_line_2 ?? "",
    city: supplier.city ?? "",
    county_or_region:
      supplier.county_or_region ?? "",
    country: supplier.country ?? "",
    postal_code: supplier.postal_code ?? "",
    tax_number: supplier.tax_number ?? "",
    registration_number:
      supplier.registration_number ?? "",
    payment_terms_days: String(
      supplier.payment_terms_days,
    ),
    credit_limit: supplier.credit_limit,
    currency: supplier.currency,
    notes: supplier.notes ?? "",
  };
}

function buildCreatePayload(
  values: SupplierFormValues,
): CreateSupplierRequest {
  return {
    supplier_code:
      values.supplier_code.trim().length > 0
        ? values.supplier_code.trim()
        : undefined,
    name: values.name.trim(),
    legal_name: textOrNull(values.legal_name),
    contact_person: textOrNull(
      values.contact_person,
    ),
    email: textOrNull(values.email),
    phone: textOrNull(values.phone),
    alternate_phone: textOrNull(
      values.alternate_phone,
    ),
    address_line_1: textOrNull(
      values.address_line_1,
    ),
    address_line_2: textOrNull(
      values.address_line_2,
    ),
    city: textOrNull(values.city),
    county_or_region: textOrNull(
      values.county_or_region,
    ),
    country: textOrNull(values.country),
    postal_code: textOrNull(values.postal_code),
    tax_number: textOrNull(values.tax_number),
    registration_number: textOrNull(
      values.registration_number,
    ),
    payment_terms_days: optionalNumber(
      values.payment_terms_days,
    ),
    credit_limit:
      values.credit_limit.trim().length > 0
        ? values.credit_limit.trim()
        : undefined,
    currency:
      values.currency.trim().length > 0
        ? values.currency.trim().toUpperCase()
        : undefined,
    notes: textOrNull(values.notes),
  };
}

function buildUpdatePayload(
  values: SupplierFormValues,
): UpdateSupplierRequest {
  const payload = buildCreatePayload(values);

  delete payload.supplier_code;

  return payload;
}

function FieldError({
  message,
}: {
  message?: string;
}) {
  if (!message) {
    return null;
  }

  return (
    <p className="text-xs text-destructive">
      {message}
    </p>
  );
}

export function SupplierFormDialog({
  open,
  mode,
  supplier,
  isSubmitting,
  errorMessage,
  onOpenChange,
  onCreate,
  onUpdate,
}: SupplierFormDialogProps) {
  const {
    control,
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setValue,
  } = useForm<SupplierFormValues>({    
    resolver: zodResolver(supplierFormSchema),
    defaultValues: emptyValues,
  });

  useEffect(() => {
    if (open) {
      reset(supplierToValues(supplier));
    }
  }, [
    open,
    reset,
    supplier,
  ]);

  const selectedCountry = useWatch({
    control,
    name: "country",
  });

  const selectedCurrency = useWatch({
    control,
    name: "currency",
  });

  const onSubmit = (
    values: SupplierFormValues,
  ) => {
    if (mode === "edit" && supplier) {
      onUpdate(
        supplier.id,
        buildUpdatePayload(values),
      );
      return;
    }

    onCreate(buildCreatePayload(values));
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {mode === "edit"
              ? "Edit Supplier"
              : "Create Supplier"}
          </DialogTitle>
          <DialogDescription>
            Maintain verified tenant-wide supplier
            master data.
          </DialogDescription>
        </DialogHeader>

        <form
          id="supplier-form"
          className="grid gap-5"
          onSubmit={handleSubmit(onSubmit)}
        >
          <div className="grid gap-4 md:grid-cols-2">
            {mode === "edit" ? (
              <div className="space-y-2">
                <Label htmlFor="supplier_code">
                  Supplier Code
                </Label>
                <Input
                  id="supplier_code"
                  autoComplete="off"
                  disabled
                  {...register("supplier_code")}
                />
                <p className="text-xs text-muted-foreground">
                  Supplier codes are assigned automatically.
                </p>
              </div>
            ) : null}

            <div className="space-y-2">
              <Label htmlFor="name">
                Supplier Name
              </Label>
              <Input
                id="name"
                autoComplete="organization"
                aria-invalid={
                  errors.name ? true : undefined
                }
                {...register("name")}
              />
              <FieldError
                message={errors.name?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="legal_name">
                Legal Name
              </Label>
              <Input
                id="legal_name"
                autoComplete="organization"
                {...register("legal_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="contact_person">
                Contact Person
              </Label>
              <Input
                id="contact_person"
                autoComplete="name"
                {...register("contact_person")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                aria-invalid={
                  errors.email ? true : undefined
                }
                {...register("email")}
              />
              <FieldError
                message={errors.email?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">
                Phone
              </Label>
              <Input
                id="phone"
                autoComplete="tel"
                {...register("phone")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="alternate_phone">
                Alternate Phone
              </Label>
              <Input
                id="alternate_phone"
                autoComplete="tel"
                {...register("alternate_phone")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="city">
                City
              </Label>
              <Input
                id="city"
                autoComplete="address-level2"
                {...register("city")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="county_or_region">
                County or Region
              </Label>
              <Input
                id="county_or_region"
                autoComplete="address-level1"
                {...register("county_or_region")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">
                Country
              </Label>
              <Select
                value={selectedCountry}
                onValueChange={(value) =>
                  setValue(
                    "country",
                    value ?? "",
                    {
                      shouldDirty: true,
                      shouldValidate: true,
                    },
                  )
                }
              >
                <SelectTrigger
                  id="country"
                  className="w-full"
                >
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRIES.map((country) => (
                    <SelectItem
                      key={country.code}
                      value={country.code}
                    >
                      {country.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="postal_code">
                Postal Code
              </Label>
              <Input
                id="postal_code"
                autoComplete="postal-code"
                {...register("postal_code")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tax_number">
                Tax Number
              </Label>
              <Input
                id="tax_number"
                {...register("tax_number")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="registration_number">
                Registration Number
              </Label>
              <Input
                id="registration_number"
                {...register("registration_number")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="payment_terms_days">
                Payment Terms Days
              </Label>
              <Input
                id="payment_terms_days"
                inputMode="numeric"
                aria-invalid={
                  errors.payment_terms_days
                    ? true
                    : undefined
                }
                {...register(
                  "payment_terms_days",
                )}
              />
              <FieldError
                message={
                  errors.payment_terms_days
                    ?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="credit_limit">
                Credit Limit
              </Label>
              <Input
                id="credit_limit"
                inputMode="decimal"
                aria-invalid={
                  errors.credit_limit
                    ? true
                    : undefined
                }
                {...register("credit_limit")}
              />
              <FieldError
                message={
                  errors.credit_limit?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">
                Currency
              </Label>
              <Select
                value={selectedCurrency}
                onValueChange={(value) =>
                  setValue(
                    "currency",
                    value ?? "",
                    {
                      shouldDirty: true,
                      shouldValidate: true,
                    },
                  )
                }
              >
                <SelectTrigger
                  id="currency"
                  className="w-full"
                >
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((currency) => (
                    <SelectItem
                      key={currency.code}
                      value={currency.code}
                    >
                      {currency.code} — {currency.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldError
                message={errors.currency?.message}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="address_line_1">
                Address Line 1
              </Label>
              <Input
                id="address_line_1"
                autoComplete="address-line1"
                {...register("address_line_1")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="address_line_2">
                Address Line 2
              </Label>
              <Input
                id="address_line_2"
                autoComplete="address-line2"
                {...register("address_line_2")}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">
              Notes
            </Label>
            <Textarea
              id="notes"
              {...register("notes")}
            />
          </div>

          {errorMessage ? (
            <p className="text-sm text-destructive">
              {errorMessage}
            </p>
          ) : null}
        </form>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form="supplier-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="animate-spin" />
            ) : null}
            {mode === "edit"
              ? "Save Supplier"
              : "Create Supplier"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
