import {
  Eye,
  Pencil,
  Power,
  RotateCcw,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Supplier } from "@/types/entities";

interface SuppliersTableProps {
  suppliers: Supplier[];
  canUpdate: boolean;
  canManageLifecycle: boolean;
  onView: (supplier: Supplier) => void;
  onEdit: (supplier: Supplier) => void;
  onLifecycle: (supplier: Supplier) => void;
}

function formatLocation(
  supplier: Supplier,
): string {
  return (
    [
      supplier.city,
      supplier.country,
    ]
      .filter(Boolean)
      .join(", ") || "Not provided"
  );
}

export function SuppliersTable({
  suppliers,
  canUpdate,
  canManageLifecycle,
  onView,
  onEdit,
  onLifecycle,
}: SuppliersTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Supplier</TableHead>
          <TableHead>Code</TableHead>
          <TableHead>Contact</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Payment Terms</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">
            Actions
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {suppliers.map((supplier) => (
          <TableRow key={supplier.id}>
            <TableCell>
              <div className="min-w-48">
                <p className="font-medium">
                  {supplier.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {supplier.email ??
                    "No email recorded"}
                </p>
              </div>
            </TableCell>
            <TableCell>
              {supplier.supplier_code}
            </TableCell>
            <TableCell>
              <div className="min-w-36">
                <p>
                  {supplier.contact_person ??
                    "Not provided"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {supplier.phone ??
                    "No phone recorded"}
                </p>
              </div>
            </TableCell>
            <TableCell>
              {formatLocation(supplier)}
            </TableCell>
            <TableCell>
              {supplier.payment_terms_days} days
            </TableCell>
            <TableCell>
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
            </TableCell>
            <TableCell>
              <div className="flex justify-end gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="View supplier"
                  onClick={() => onView(supplier)}
                >
                  <Eye />
                  <span className="sr-only">
                    View supplier
                  </span>
                </Button>

                {canUpdate ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Edit supplier"
                    onClick={() => onEdit(supplier)}
                  >
                    <Pencil />
                    <span className="sr-only">
                      Edit supplier
                    </span>
                  </Button>
                ) : null}

                {canManageLifecycle ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title={
                      supplier.is_active
                        ? "Deactivate supplier"
                        : "Reactivate supplier"
                    }
                    onClick={() =>
                      onLifecycle(supplier)
                    }
                  >
                    {supplier.is_active ? (
                      <Power />
                    ) : (
                      <RotateCcw />
                    )}
                    <span className="sr-only">
                      {supplier.is_active
                        ? "Deactivate supplier"
                        : "Reactivate supplier"}
                    </span>
                  </Button>
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
