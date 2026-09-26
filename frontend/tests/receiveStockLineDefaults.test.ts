import assert from "node:assert/strict";
import test from "node:test";

import {
  createReceiptLineDefaults,
} from "../src/features/inventory/lib/receiptLineDefaults.ts";

test(
  "new goods receipt lines do not invent a Stock Qty of 1",
  () => {
    const line = createReceiptLineDefaults("125.00");

    assert.equal(
      line.quantity,
      "",
      "Stock Qty must start blank so the cashier explicitly confirms inventory quantity",
    );

    assert.equal(line.invoiced_quantity, "");
    assert.equal(line.received_quantity, "");
    assert.equal(line.accepted_quantity, "");
    assert.equal(line.rejected_quantity, "");
    assert.equal(line.bonus_quantity, "");

    assert.equal(line.unit_cost, "125.00");
  },
);

test(
  "new goods receipt lines fall back to zero cost without inventing quantity",
  () => {
    const line = createReceiptLineDefaults(null);

    assert.equal(line.quantity, "");
    assert.equal(line.unit_cost, "0.00");
  },
);
