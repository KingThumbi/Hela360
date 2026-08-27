import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Supplier } from "@/types/entities";

interface SupplierDetailDialogProps {
  open: boolean;
  supplier: Supplier | null;
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

export function SupplierDetailDialog({
  open,
  supplier,
  onOpenChange,
}: SupplierDetailDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {supplier?.name ?? "Supplier"}
          </DialogTitle>
          <DialogDescription>
            Verified supplier master record.
          </DialogDescription>
        </DialogHeader>

        {supplier ? (
          <dl className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Badge
                variant={
                  supplier.is_active
                    ? "secondary"
                    : "outline"
                }
              >
                {supplier.is_active
                  ? "Active"
                  : "Inactive"}
              </Badge>
            </div>
            <DetailItem
              label="Supplier Code"
              value={supplier.supplier_code}
            />
            <DetailItem
              label="Legal Name"
              value={supplier.legal_name}
            />
            <DetailItem
              label="Contact Person"
              value={supplier.contact_person}
            />
            <DetailItem
              label="Email"
              value={supplier.email}
            />
            <DetailItem
              label="Phone"
              value={supplier.phone}
            />
            <DetailItem
              label="Alternate Phone"
              value={supplier.alternate_phone}
            />
            <DetailItem
              label="Location"
              value={
                [
                  supplier.city,
                  supplier.county_or_region,
                  supplier.country,
                ]
                  .filter(Boolean)
                  .join(", ") || null
              }
            />
            <DetailItem
              label="Postal Code"
              value={supplier.postal_code}
            />
            <DetailItem
              label="Tax Number"
              value={supplier.tax_number}
            />
            <DetailItem
              label="Registration Number"
              value={supplier.registration_number}
            />
            <DetailItem
              label="Payment Terms"
              value={`${supplier.payment_terms_days} days`}
            />
            <DetailItem
              label="Credit Limit"
              value={`${supplier.currency} ${supplier.credit_limit}`}
            />
            <DetailItem
              label="Address Line 1"
              value={supplier.address_line_1}
            />
            <DetailItem
              label="Address Line 2"
              value={supplier.address_line_2}
            />
            <div className="space-y-1 md:col-span-2">
              <dt className="text-xs font-medium uppercase text-muted-foreground">
                Notes
              </dt>
              <dd className="whitespace-pre-wrap text-sm">
                {supplier.notes ?? "Not provided"}
              </dd>
            </div>
          </dl>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
