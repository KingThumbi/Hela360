import { Eye } from "lucide-react";

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
import type { Customer } from "@/types/entities";

interface CustomersTableProps {
  customers: Customer[];
  onView: (customer: Customer) => void;
}

function formatContact(
  customer: Customer,
): string {
  return (
    [
      customer.phone,
      customer.email,
    ]
      .filter(Boolean)
      .join(" · ") || "Not provided"
  );
}

export function CustomersTable({
  customers,
  onView,
}: CustomersTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead>Number</TableHead>
          <TableHead>Contact</TableHead>
          <TableHead>City</TableHead>
          <TableHead>Loyalty</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">
            Actions
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {customers.map((customer) => (
          <TableRow key={customer.id}>
            <TableCell>
              <div className="min-w-48">
                <p className="font-medium">
                  {customer.full_name ||
                    customer.first_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {customer.id_number ??
                    "No ID recorded"}
                </p>
              </div>
            </TableCell>
            <TableCell>
              {customer.customer_number}
            </TableCell>
            <TableCell>
              <div className="min-w-44">
                {formatContact(customer)}
              </div>
            </TableCell>
            <TableCell>
              {customer.city ?? "Not provided"}
            </TableCell>
            <TableCell>
              {customer.loyalty_points}
            </TableCell>
            <TableCell>
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
            </TableCell>
            <TableCell>
              <div className="flex justify-end gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="View customer"
                  onClick={() => onView(customer)}
                >
                  <Eye />
                  <span className="sr-only">
                    View customer
                  </span>
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
