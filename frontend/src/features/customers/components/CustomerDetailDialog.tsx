import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCustomer } from "@/hooks/queries/customers";

interface CustomerDetailDialogProps {
  open: boolean;
  customerId: string | null;
  onOpenChange: (open: boolean) => void;
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string | number | null;
}) {
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium uppercase text-muted-foreground">
        {label}
      </dt>
      <dd className="text-sm">
        {value ?? "Not provided"}
      </dd>
    </div>
  );
}

export function CustomerDetailDialog({
  open,
  customerId,
  onOpenChange,
}: CustomerDetailDialogProps) {
  const customerQuery = useCustomer(
    customerId ?? "",
    {
      enabled: open && Boolean(customerId),
    },
  );

  const customer = customerQuery.data ?? null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {customer?.full_name ?? "Customer"}
          </DialogTitle>
          <DialogDescription>
            Verified customer master record.
          </DialogDescription>
        </DialogHeader>

        {customer ? (
          <dl className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Badge
                variant={
                  customer.is_active
                    ? "secondary"
                    : "outline"
                }
              >
                {customer.is_active
                  ? "Active"
                  : "Inactive"}
              </Badge>
            </div>
            <DetailItem
              label="Customer Number"
              value={customer.customer_number}
            />
            <DetailItem
              label="First Name"
              value={customer.first_name}
            />
            <DetailItem
              label="Other Names"
              value={customer.other_names}
            />
            <DetailItem
              label="Last Name"
              value={customer.last_name}
            />
            <DetailItem
              label="Phone"
              value={customer.phone}
            />
            <DetailItem
              label="Email"
              value={customer.email}
            />
            <DetailItem
              label="Gender"
              value={customer.gender}
            />
            <DetailItem
              label="Date of Birth"
              value={customer.date_of_birth}
            />
            <DetailItem
              label="ID Number"
              value={customer.id_number}
            />
            <DetailItem
              label="City"
              value={customer.city}
            />
            <DetailItem
              label="Loyalty Points"
              value={customer.loyalty_points}
            />
            <div className="space-y-1 md:col-span-2">
              <dt className="text-xs font-medium uppercase text-muted-foreground">
                Address
              </dt>
              <dd className="whitespace-pre-wrap text-sm">
                {customer.address ?? "Not provided"}
              </dd>
            </div>
          </dl>
        ) : customerQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">
            Loading customer details...
          </p>
        ) : customerQuery.isError ? (
          <p className="text-sm text-destructive">
            {customerQuery.error instanceof Error
              ? customerQuery.error.message
              : "Customer details could not be loaded."}
          </p>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
