import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

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
import { Textarea } from "@/components/ui/textarea";
import type { CreateCustomerRequest } from "@/types/requests";
import {
  customerFormSchema,
  type CustomerFormValues,
} from "@/validation/customerSchema";

interface CustomerFormDialogProps {
  open: boolean;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onOpenChange: (open: boolean) => void;
  onCreate: (payload: CreateCustomerRequest) => void;
}

const emptyValues: CustomerFormValues = {
  customer_number: "",
  first_name: "",
  last_name: "",
  other_names: "",
  phone: "",
  email: "",
  gender: "",
  date_of_birth: "",
  id_number: "",
  address: "",
  city: "",
};

function textOrUndefined(
  value: string,
): string | undefined {
  const trimmed = value.trim();

  return trimmed.length > 0
    ? trimmed
    : undefined;
}

function buildCreatePayload(
  values: CustomerFormValues,
): CreateCustomerRequest {
  return {
    first_name: values.first_name.trim(),
    customer_number: textOrUndefined(
      values.customer_number,
    ),
    last_name: textOrUndefined(
      values.last_name,
    ),
    other_names: textOrUndefined(
      values.other_names,
    ),
    phone: textOrUndefined(values.phone),
    email: textOrUndefined(
      values.email,
    )?.toLowerCase(),
    gender: textOrUndefined(values.gender),
    date_of_birth: textOrUndefined(
      values.date_of_birth,
    ),
    id_number: textOrUndefined(
      values.id_number,
    ),
    address: textOrUndefined(values.address),
    city: textOrUndefined(values.city),
  };
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

export function CustomerFormDialog({
  open,
  isSubmitting,
  errorMessage,
  onOpenChange,
  onCreate,
}: CustomerFormDialogProps) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<CustomerFormValues>({
    resolver: zodResolver(customerFormSchema),
    defaultValues: emptyValues,
  });

  useEffect(() => {
    if (open) {
      reset(emptyValues);
    }
  }, [
    open,
    reset,
  ]);

  const onSubmit = (
    values: CustomerFormValues,
  ) => {
    onCreate(buildCreatePayload(values));
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Create Customer
          </DialogTitle>
          <DialogDescription>
            Add a tenant customer master record.
          </DialogDescription>
        </DialogHeader>

        <form
          className="space-y-5"
          onSubmit={handleSubmit(onSubmit)}
        >
          {errorMessage ? (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {errorMessage}
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="customer_number">
                Customer Number
              </Label>
              <Input
                id="customer_number"
                {...register("customer_number")}
                placeholder="Auto-generated if empty"
              />
              <FieldError
                message={
                  errors.customer_number?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="first_name">
                First Name
              </Label>
              <Input
                id="first_name"
                {...register("first_name")}
              />
              <FieldError
                message={errors.first_name?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="other_names">
                Other Names
              </Label>
              <Input
                id="other_names"
                {...register("other_names")}
              />
              <FieldError
                message={
                  errors.other_names?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="last_name">
                Last Name
              </Label>
              <Input
                id="last_name"
                {...register("last_name")}
              />
              <FieldError
                message={errors.last_name?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">
                Phone
              </Label>
              <Input
                id="phone"
                {...register("phone")}
              />
              <FieldError
                message={errors.phone?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                {...register("email")}
              />
              <FieldError
                message={errors.email?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">
                Gender
              </Label>
              <Input
                id="gender"
                {...register("gender")}
              />
              <FieldError
                message={errors.gender?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="date_of_birth">
                Date of Birth
              </Label>
              <Input
                id="date_of_birth"
                type="date"
                {...register("date_of_birth")}
              />
              <FieldError
                message={
                  errors.date_of_birth?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="id_number">
                ID Number
              </Label>
              <Input
                id="id_number"
                {...register("id_number")}
              />
              <FieldError
                message={errors.id_number?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="city">
                City
              </Label>
              <Input
                id="city"
                {...register("city")}
              />
              <FieldError
                message={errors.city?.message}
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="address">
                Address
              </Label>
              <Textarea
                id="address"
                {...register("address")}
                rows={3}
              />
              <FieldError
                message={errors.address?.message}
              />
            </div>
          </div>

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
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="animate-spin" />
              ) : null}
              Create Customer
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
