import {
  Barcode,
  FileText,
  Minus,
  Plus,
  Search,
  ShoppingCart,
  Trash2,
} from "lucide-react";
import {
  type ReactNode,
  useMemo,
  useState,
} from "react";
import {
  Link,
} from "react-router-dom";
import { toast } from "sonner";

import {
  Page,
  PageContent,
} from "@/components/page";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateSale,
  usePosProductAvailability,
} from "@/hooks/queries/sales";
import {
  useCustomers,
} from "@/hooks/queries/customers";
import {
  usePaymentMethods,
} from "@/hooks/queries/payment-methods";
import {
  useProductByCode,
  useProducts,
  useProductUnits,
} from "@/hooks/queries/products";
import {
  useCloseTillShift,
  useCurrentTillShift,
  useOpenTillShift,
  useTakeoverTillShift,
  useTills,
} from "@/hooks/queries/tills";
import { useQueryScope } from "@/hooks/useQueryScope";
import { createClientId } from "@/lib/clientId";
import { PATHS } from "@/routes/routes";
import { useAuthStore } from "@/store/authStore";
import type {
  Customer,
  PaymentMethod,
  Product,
  ProductUnit,
} from "@/types/entities";
import type {
  CreateSalePrescriptionContext,
  CreateSaleRequest,
} from "@/types/requests";
import type {
  Branch as SessionBranch,
} from "@/types/auth";
import type {
  PosProductAvailability,
} from "@/types/responses";

const PRODUCT_PAGE_SIZE = 8;
const CUSTOMER_PAGE_SIZE = 8;

interface CartItem {
  product: Product;
  quantity: string;
  unit: ProductUnit | null;

  /**
   * Transaction selling price entered by the cashier.
   *
   * The marked and minimum prices remain owned by Product /
   * ProductUnit. This field represents only the price applied
   * to this sale.
   */
  sellingPrice: string;
}

interface PaymentEntry {
  id: string;
  payment_method_id: string;
  amount: string;
  reference: string;
}

interface PrescriptionDraft {
  prescription_reference: string;
  prescriber_name: string;
  prescriber_registration_number: string;
  prescription_date: string;
  notes: string;
}

function productUnitLabel(
  productUnit: ProductUnit,
): string {
  const unitName =
    productUnit.unit?.name ??
    productUnit.unit?.code ??
    "Unit";

  const factor = decimalValue(
    productUnit.conversion_factor_to_base,
  );

  const price =
    productUnit.sale_price !== null
      ? ` · ${money(decimalValue(productUnit.sale_price))}`
      : " · price unset";

  const conversion =
    factor !== 1
      ? ` · ×${factor}`
      : "";

  return `${unitName}${conversion}${price}`;
}

function emptyPrescriptionDraft(): PrescriptionDraft {
  return {
    prescription_reference: "",
    prescriber_name: "",
    prescriber_registration_number: "",
    prescription_date: "",
    notes: "",
  };
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function decimalValue(value: string | null): number {
  if (!value) {
    return 0;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : 0;
}

function quantityValue(value: string): number {
  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : 0;
}

function cartMarkedUnitPrice(
  item: CartItem,
): number {
  const price =
    item.unit?.sale_price ??
    item.product.default_sale_price;

  return decimalValue(price);
}

function cartMinimumUnitPrice(
  item: CartItem,
): number | null {
  const price =
    item.unit?.minimum_sale_price ??
    item.product.min_sale_price;

  if (price === null) {
    return null;
  }

  return decimalValue(price);
}

function cartUnitPrice(
  item: CartItem,
): number {
  return decimalValue(
    item.sellingPrice,
  );
}

function cartConversionFactor(
  item: CartItem,
): number {
  if (!item.unit) {
    return 1;
  }

  const factor = decimalValue(
    item.unit.conversion_factor_to_base,
  );

  return factor > 0 ? factor : 1;
}

function cartBaseQuantity(
  item: CartItem,
): number {
  return (
    quantityValue(item.quantity) *
    cartConversionFactor(item)
  );
}

function cartLineTotal(
  item: CartItem,
): number {
  return (
    cartUnitPrice(item) *
    quantityValue(item.quantity)
  );
}

function money(value: number): string {
  return value.toFixed(2);
}

function quantity(value: string | null): string {
  if (value === null) {
    return "Not tracked";
  }
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        maximumFractionDigits: 4,
      })
    : value;
}

function dateLabel(value: string | null): string {
  if (!value) {
    return "None";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function displayProductCode(product: Product): string {
  return product.internal_sku || product.codes[0]?.code_value || product.id;
}

function branchName(
  branches: SessionBranch[],
  branchId: string | null,
): string {
  return branches.find((branch) => branch.id === branchId)?.name ?? "No branch selected";
}

function makePaymentEntry(): PaymentEntry {
  return {
    id: createClientId(),
    payment_method_id: "",
    amount: "",
    reference: "",
  };
}

function checkoutErrorMessage(error: unknown): string {
  const message = errorMessage(error);
  const normalized = message.toLowerCase();

  if (
    normalized.includes("insufficient stock") ||
    normalized.includes("insufficient sellable") ||
    normalized.includes("no stock balance")
  ) {
    return "Stock changed. Review cart quantities and try again.";
  }
  if (normalized.includes("no open shift")) {
    return "Till shift changed. Reopen or refresh the shift before checkout.";
  }
  if (normalized.includes("payment")) {
    return message;
  }
  if (
    normalized.includes(
      "unit_price cannot be below min_sale_price",
    )
  ) {
    return "Selling price is below the permitted minimum price.";
  }

  if (
    normalized.includes(
      "default_sale_price",
    )
  ) {
    return "The product does not have a valid selling price configured.";
  }

  if (
    normalized.includes("unit_price") ||
    normalized.includes("min_sale_price")
  ) {
    return message;
  }

  return message;
}

function availabilityMap(
  items: PosProductAvailability[] | undefined,
): Map<string, PosProductAvailability> {
  return new Map((items ?? []).map((item) => [item.product_id, item]));
}

function isCashPaymentMethod(
  paymentMethodId: string,
  paymentMethods: PaymentMethod[],
): boolean {
  return paymentMethods.some(
    (method) =>
      method.id === paymentMethodId &&
      method.method_type === "cash",
  );
}

export function PosPage() {
  const {
    branchId,
    isBranchScopeReady,
  } = useQueryScope();
  const branches = useAuthStore(
    (state) => state.accessibleBranches,
  );

  const [
    productSearchInput,
    setProductSearchInput,
  ] = useState("");
  const [
    submittedProductSearch,
    setSubmittedProductSearch,
  ] = useState("");
  const [
    codeInput,
    setCodeInput,
  ] = useState("");
  const [
    submittedCode,
    setSubmittedCode,
  ] = useState("");
  const [
    customerSearchInput,
    setCustomerSearchInput,
  ] = useState("");
  const [
    submittedCustomerSearch,
    setSubmittedCustomerSearch,
  ] = useState("");
  const [
    selectedCustomer,
    setSelectedCustomer,
  ] = useState<Customer | null>(null);
  const [
    selectedTillId,
    setSelectedTillId,
  ] = useState("");
  const [
    openingFloat,
    setOpeningFloat,
  ] = useState("0.00");
  const [
    cartItems,
    setCartItems,
  ] = useState<CartItem[]>([]);
  const [
    prescriptionDrafts,
    setPrescriptionDrafts,
  ] = useState<Record<string, PrescriptionDraft>>({});
  const [
    payments,
    setPayments,
  ] = useState<PaymentEntry[]>([
    makePaymentEntry(),
  ]);
  const [
    checkoutError,
    setCheckoutError,
  ] = useState<string | null>(null);
  const [
    lastSaleNumber,
    setLastSaleNumber,
  ] = useState<string | null>(null);
  const [
    lastSaleId,
    setLastSaleId,
  ] = useState<string | null>(null);

    const [
    takeoverShiftOpen,
    setTakeoverShiftOpen,
  ] = useState(false);

  const [
    closeShiftOpen,
    setCloseShiftOpen,
  ] = useState(false);

  const [
    closingCash,
    setClosingCash,
  ] = useState("");

  const [
    closingNotes,
    setClosingNotes,
  ] = useState("");

  const [
    reconciliationOpen,
    setReconciliationOpen,
  ] = useState(false);

  const [
    lastReconciliation,
    setLastReconciliation,
  ] = useState<{
    opening_float: string;
    cash_sales_total: string;
    expected_cash: string;
    closing_cash: string;
    cash_difference: string;
  } | null>(null);

  const productParams = useMemo(
    () => ({
      page: 1,
      per_page: PRODUCT_PAGE_SIZE,
      search:
        submittedProductSearch.trim().length > 0
          ? submittedProductSearch.trim()
          : undefined,
      is_active: true,
    }),
    [submittedProductSearch],
  );
  const customerParams = useMemo(
    () => ({
      page: 1,
      per_page: CUSTOMER_PAGE_SIZE,
      search:
        submittedCustomerSearch.trim().length > 0
          ? submittedCustomerSearch.trim()
          : undefined,
    }),
    [submittedCustomerSearch],
  );

  const tillsQuery = useTills();
  const currentShiftQuery = useCurrentTillShift();  
  const openTillShift = useOpenTillShift();
  const closeTillShift = useCloseTillShift();
  const takeoverTillShift = useTakeoverTillShift();
  const productsQuery = useProducts(productParams);
  const productByCodeQuery = useProductByCode(
    submittedCode,
    {
      enabled: submittedCode.trim().length > 0,
    },
  );
  const customersQuery = useCustomers(customerParams);
  const paymentMethodsQuery = usePaymentMethods();
  const createSale = useCreateSale();

  const currentShift = currentShiftQuery.data ?? null;
  const shiftOwnedByCurrentSession =
    currentShift?.owned_by_current_session ?? false;

  const shiftRequiresTakeover =
    Boolean(currentShift) &&
    !shiftOwnedByCurrentSession;

  const tills = tillsQuery.data ?? [];
  const products = useMemo(
    () => productsQuery.data?.items ?? [],
    [productsQuery.data?.items],
  );
  const customers = customersQuery.data?.items ?? [];
  const paymentMethods = paymentMethodsQuery.data ?? [];
  const activeTill = tills.find(
    (till) =>
      till.id === (currentShift?.till_id ?? selectedTillId),
  );
  const availabilityProductIds = useMemo(
    () => [
      ...new Set(
        [
          ...products.map((product) => product.id),
          ...(productByCodeQuery.data
            ? [productByCodeQuery.data.id]
            : []),
          ...cartItems.map((item) => item.product.id),
        ].filter(Boolean),
      ),
    ],
    [
      cartItems,
      productByCodeQuery.data,
      products,
    ],
  );
  const availabilityQuery = usePosProductAvailability({
    tillId: activeTill?.id,
    productIds: availabilityProductIds,
  });
  const productAvailability = useMemo(
    () => availabilityMap(availabilityQuery.data),
    [availabilityQuery.data],
  );


  const estimatedTotal = cartItems.reduce(
    (total, item) =>
      total + cartLineTotal(item),
    0,
  );

  const paymentSummary = payments.reduce(
    (
      summary,
      payment,
    ) => {
      const enteredAmount =
        quantityValue(payment.amount);

      if (enteredAmount <= 0) {
        return summary;
      }

      const remainingBeforePayment =
        summary.remainingBalance;

      const amountApplied = Math.min(
        enteredAmount,
        remainingBeforePayment,
      );

      const isCash =
        isCashPaymentMethod(
          payment.payment_method_id,
          paymentMethods,
        );

      const cashChange =
        isCash
          ? Math.max(
              0,
              enteredAmount -
                remainingBeforePayment,
            )
          : 0;

      return {
        tenderedTotal:
          summary.tenderedTotal +
          enteredAmount,

        remainingBalance: Math.max(
          0,
          remainingBeforePayment -
            amountApplied,
        ),

        changeDue:
          summary.changeDue +
          cashChange,
      };
    },
    {
      tenderedTotal: 0,
      remainingBalance: estimatedTotal,
      changeDue: 0,
    },
  );

  const tenderedTotal =
    paymentSummary.tenderedTotal;

  const amountDue =
    paymentSummary.remainingBalance;

  const changeDue =
    paymentSummary.changeDue;

  const paymentSatisfied =
    estimatedTotal > 0 &&
    amountDue <= 0;
    
  const addProduct = (product: Product) => {
    const availability = productAvailability.get(product.id);
    if (
      product.track_inventory &&
      availability &&
      availability.status === "out_of_stock"
    ) {
      toast.error("This Product has no sellable stock for the selected Till Warehouse.");
      return;
    }

    setCheckoutError(null);
    setLastSaleNumber(null);
    setLastSaleId(null);
    setCartItems((items) => {
      const existing = items.find(
        (item) => item.product.id === product.id,
      );

      if (!existing) {
        if (product.requires_prescription) {
          setPrescriptionDrafts((drafts) => ({
            ...drafts,
            [product.id]: drafts[product.id] ?? emptyPrescriptionDraft(),
          }));
        }

        return [
          ...items,
          {
            product,
            quantity: "1",
            unit: null,
            sellingPrice:
              product.default_sale_price ??
              "",
          },
        ];
      }

      return items.map((item) =>
        item.product.id === product.id
          ? {
              ...item,
              quantity: String(
                quantityValue(item.quantity) + 1,
              ),
            }
          : item,
      );
    });
  };

  const updateCartQuantity = (
    productId: string,
    quantity: string,
  ) => {
    setCartItems((items) =>
      items.map((item) =>
        item.product.id === productId
          ? {
              ...item,
              quantity,
            }
          : item,
      ),
    );
  };

  const updateCartSellingPrice = (
    productId: string,
    sellingPrice: string,
  ) => {
    setCheckoutError(null);

    setCartItems((items) =>
      items.map((item) =>
        item.product.id === productId
          ? {
              ...item,
              sellingPrice,
            }
          : item,
      ),
    );
  };

  const updateCartUnit = (
    productId: string,
    unit: ProductUnit | null,
  ) => {
    setCheckoutError(null);

    setCartItems((items) =>
      items.map((item) =>
        item.product.id === productId
          ? {
              ...item,
              unit,
              sellingPrice:
                unit?.sale_price ??
                item.product.default_sale_price ??
                "",
            }
          : item,
      ),
    );
  };

  const removeCartItem = (productId: string) => {
    setCartItems((items) =>
      items.filter((item) => item.product.id !== productId),
    );

    setPrescriptionDrafts((drafts) => {
      const next = {
        ...drafts,
      };

      delete next[productId];

      return next;
    });
  };
  const updatePrescriptionDraft = (
    productId: string,
    patch: Partial<PrescriptionDraft>,
  ) => {
    setPrescriptionDrafts((drafts) => ({
      ...drafts,
      [productId]: {
        ...(drafts[productId] ?? emptyPrescriptionDraft()),
        ...patch,
      },
    }));
  };

  const prescriptionContextForProduct = (
    productId: string,
  ): CreateSalePrescriptionContext => {
    const draft =
      prescriptionDrafts[productId] ?? emptyPrescriptionDraft();
    const context: CreateSalePrescriptionContext = {
      prescriber_name: draft.prescriber_name.trim(),
    };

    if (draft.prescription_reference.trim()) {
      context.prescription_reference =
        draft.prescription_reference.trim();
    }

    if (draft.prescriber_registration_number.trim()) {
      context.prescriber_registration_number =
        draft.prescriber_registration_number.trim();
    }

    if (draft.prescription_date) {
      context.prescription_date = draft.prescription_date;
    }

    if (draft.notes.trim()) {
      context.notes = draft.notes.trim();
    }

    return context;
  };

  const updatePayment = (
    id: string,
    patch: Partial<PaymentEntry>,
  ) => {
    setPayments((entries) =>
      entries.map((entry) =>
        entry.id === id
          ? {
              ...entry,
              ...patch,
            }
          : entry,
      ),
    );
  };

  const removePayment = (id: string) => {
    setPayments((entries) =>
      entries.length <= 1
        ? entries
        : entries.filter((entry) => entry.id !== id),
    );
  };

  const openShift = () => {
    if (!selectedTillId) {
      toast.error("Select an active till first.");
      return;
    }

    if (!activeTill?.warehouse_id) {
      toast.error("Selected till is not configured with a warehouse.");
      return;
    }

    openTillShift.mutate(
      {
        till_id: selectedTillId,
        opening_float: openingFloat || "0.00",
      },
      {
        onSuccess: () => {
          toast.success("Till shift opened.");
        },
        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  async function takeoverShift() {
    if (!currentShift) {
      toast.error(
        "There is no active till shift to take over.",
      );
      return;
    }

    try {
      await takeoverTillShift.mutateAsync(
        currentShift.id,
      );

      setCheckoutError(null);
      setTakeoverShiftOpen(false);

      toast.success(
        "Till shift transferred to this device.",
      );
    } catch (error) {
      toast.error(
        errorMessage(error),
      );
    }
  }

    async function closeShift() {
    if (!currentShift) {
      toast.error(
        "There is no active till shift to close.",
      );
      return;
    }

    const normalizedClosingCash =
      closingCash.trim();

    if (!normalizedClosingCash) {
      toast.error(
        "Enter the cash counted in the drawer.",
      );
      return;
    }

    const closingCashValue = Number(
      normalizedClosingCash,
    );

    if (
      !Number.isFinite(closingCashValue) ||
      closingCashValue < 0
    ) {
      toast.error(
        "Closing cash must be a valid non-negative amount.",
      );
      return;
    }

    try {
      const result =
        await closeTillShift.mutateAsync({
          id: currentShift.id,
          payload: {
            closing_cash:
              closingCashValue.toFixed(2),
            notes:
              closingNotes.trim() || null,
          },
        });

      setLastReconciliation(
        result.reconciliation,
      );

      setCloseShiftOpen(false);
      setClosingCash("");
      setClosingNotes("");

      setReconciliationOpen(true);

      toast.success(
        "Till shift closed successfully.",
      );
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  const submitCheckout = () => {
    setCheckoutError(null);

    if (!currentShift) {
      setCheckoutError("Open a till shift before checkout.");
      return;
    }

    if (!currentShift.owned_by_current_session) {
      setCheckoutError(
        "This till shift is active on another session. Take over the shift before checkout.",
      );
      return;
    }

    if (!activeTill?.warehouse_id) {
      setCheckoutError("Selected till is not configured with a warehouse.");
      return;
    }

    const invalidCartItem = cartItems.find(
      (item) => quantityValue(item.quantity) <= 0,
    );
    if (cartItems.length === 0 || invalidCartItem) {
      setCheckoutError("Cart quantities must be greater than zero.");
      return;
    }

    const invalidSellingPriceItem =
      cartItems.find((item) => {
        const value = Number(
          item.sellingPrice,
        );

        return (
          item.sellingPrice.trim() === "" ||
          !Number.isFinite(value) ||
          value < 0
        );
      });

    if (invalidSellingPriceItem) {
      setCheckoutError(
        `Enter a valid selling price for ${invalidSellingPriceItem.product.name}.`,
      );
      return;
    }

    const belowMinimumItem =
      cartItems.find((item) => {
        const minimumPrice =
          cartMinimumUnitPrice(item);

        if (minimumPrice === null) {
          return false;
        }

        return (
          cartUnitPrice(item) <
          minimumPrice
        );
      });

    if (belowMinimumItem) {
      const minimumPrice =
        cartMinimumUnitPrice(
          belowMinimumItem,
        );

      setCheckoutError(
        `${belowMinimumItem.product.name} cannot be sold below ${money(
          minimumPrice ?? 0,
        )}.`,
      );

      return;
    }

  const overAvailableItem = cartItems.find((item) => {
    const availability = productAvailability.get(
      item.product.id,
    );

    if (
      !item.product.track_inventory ||
      !availability ||
      availability.sellable_quantity === null
    ) {
      return false;
    }

    const requiredBaseQuantity =
      cartBaseQuantity(item);

    const sellableBaseQuantity =
      decimalValue(
        availability.sellable_quantity,
      );

    return (
      requiredBaseQuantity >
      sellableBaseQuantity
    );
  });

  if (overAvailableItem) {
    const availability =
      productAvailability.get(
        overAvailableItem.product.id,
      );

    const requiredBaseQuantity =
      cartBaseQuantity(
        overAvailableItem,
      );

    const sellableBaseQuantity =
      decimalValue(
        availability?.sellable_quantity ?? null,
      );

    setCheckoutError(
      `${overAvailableItem.product.name} requires ${requiredBaseQuantity.toLocaleString(
        undefined,
        {
          maximumFractionDigits: 4,
        },
      )} base units, but only ${sellableBaseQuantity.toLocaleString(
        undefined,
        {
          maximumFractionDigits: 4,
        },
      )} are currently sellable in this Till Warehouse.`,
    );

    return;
  }
    const validPayments = payments.filter(
      (payment) =>
        payment.payment_method_id &&
        quantityValue(payment.amount) > 0,
    );
    if (validPayments.length === 0) {
      setCheckoutError("Add at least one payment amount.");
      return;
    }

    let remainingPaymentBalance =
    estimatedTotal;

  for (const payment of validPayments) {
    const method = paymentMethods.find(
      (entry) =>
        entry.id ===
        payment.payment_method_id,
    );

    if (!method) {
      setCheckoutError(
        "One of the selected payment methods is no longer available.",
      );
      return;
    }

    const enteredAmount =
      quantityValue(payment.amount);

    if (remainingPaymentBalance <= 0) {
      setCheckoutError(
        "Remove payment entries entered after the sale balance was fully settled.",
      );
      return;
    }

    const isCash =
      method.method_type === "cash";

    if (
      !isCash &&
      enteredAmount >
        remainingPaymentBalance + 0.005
    ) {
      setCheckoutError(
        `${method.name} payment cannot exceed the remaining balance of ${money(
          remainingPaymentBalance,
        )}.`,
      );
      return;
    }

    remainingPaymentBalance = Math.max(
      0,
      remainingPaymentBalance -
        enteredAmount,
    );
  }

    const prescriptionItems = cartItems.filter(
      (item) => item.product.requires_prescription,
    );
    if (prescriptionItems.length > 0 && !selectedCustomer) {
      setCheckoutError("Select a customer before dispensing prescription products.");
      return;
    }

    const missingPrescription = prescriptionItems.find(
      (item) =>
        !(
          prescriptionDrafts[item.product.id]?.prescriber_name.trim()
        ),
    );
    if (missingPrescription) {
      setCheckoutError(
        `Add prescriber details for ${missingPrescription.product.name}.`,
      );
      return;
    }

    let remainingAmountToApply =
    estimatedTotal;

  const appliedPayments = validPayments
    .map((payment) => {
      const tenderedAmount =
        quantityValue(payment.amount);

      if (
        tenderedAmount <= 0 ||
        remainingAmountToApply <= 0
      ) {
        return null;
      }

      const cashPayment =
        isCashPaymentMethod(
          payment.payment_method_id,
          paymentMethods,
        );

      const amountToApply = cashPayment
        ? Math.min(
            tenderedAmount,
            remainingAmountToApply,
          )
        : tenderedAmount;

      remainingAmountToApply = Math.max(
        0,
        remainingAmountToApply -
          amountToApply,
      );

      return {
        payment_method_id:
          payment.payment_method_id,

        amount:
          amountToApply.toFixed(2),

        ...(payment.reference.trim()
          ? {
              reference:
                payment.reference.trim(),
            }
          : {}),
      };
    })
    .filter(
      (
        payment,
      ): payment is NonNullable<
        typeof payment
      > => payment !== null,
    );

    const payload: CreateSaleRequest = {
      till_id: currentShift.till_id,

      ...(selectedCustomer
        ? {
            customer_id: selectedCustomer.id,
          }
        : {}),

      items: cartItems.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
        unit_price: item.sellingPrice,

        ...(item.unit
          ? {
              product_unit_id: item.unit.id,
            }
          : {}),

        ...(item.product.requires_prescription
          ? {
              prescription:
                prescriptionContextForProduct(
                  item.product.id,
                ),
            }
          : {}),
      })),

      payments: appliedPayments,
    };
    createSale.mutate(payload, {
      onSuccess: (sale) => {
        toast.success("Sale checkout completed.");
        availabilityQuery.refetch();
        setLastSaleNumber(sale.sale_number);
        setLastSaleId(sale.id);
        setCartItems([]);
        setPrescriptionDrafts({});
        setPayments([
          makePaymentEntry(),
        ]);
        setSelectedCustomer(null);
      },
      onError: (error) => {
        setCheckoutError(checkoutErrorMessage(error));
        availabilityQuery.refetch();
        currentShiftQuery.refetch();
      },
    });
  };

  const checkoutDisabledReason = (() => {
    if (createSale.isPending) {
      return "Sale is being processed.";
    }

    if (!isBranchScopeReady) {
      return "Select an active branch.";
    }

    if (!currentShift) {
      return "Open a till shift before completing the sale.";
    }

    if (!shiftOwnedByCurrentSession) {
      return "Continue on this device before completing the sale.";
    }

    if (!activeTill?.warehouse_id) {
      return "The selected till requires an assigned warehouse.";
    }

    if (cartItems.length === 0) {
      return "Add at least one product to the cart.";
    }

    if (!paymentSatisfied) {
      return `Payment balance of ${money(
        amountDue,
      )} remains.`;
    }

    return null;
  })();

  const isCheckoutDisabled =
    checkoutDisabledReason !== null;

  const isPosOperational =
    isBranchScopeReady &&
    Boolean(currentShift) &&
    shiftOwnedByCurrentSession &&
    Boolean(activeTill?.warehouse_id);

  return (
    <Page className="gap-4">
      <PageContent className="gap-4">
        {/* ================================================================
         * POS Header
         * ================================================================ */}
        <section
          className="
            flex
            flex-col
            gap-3
            rounded-xl
            border
            bg-background
            px-4
            py-3
            lg:flex-row
            lg:items-center
            lg:justify-between
          "
        >
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight">
                Point of Sale
              </h1>

              <Badge
                variant={
                  currentShift
                    ? "outline"
                    : "secondary"
                }
              >
                {currentShift
                  ? "Shift open"
                  : "Shift closed"}
              </Badge>
            </div>

            <div
              className="
                mt-1
                flex
                flex-wrap
                gap-x-4
                gap-y-1
                text-xs
                text-muted-foreground
              "
            >
              <span>
                Branch:{" "}
                <strong className="font-medium text-foreground">
                  {branchName(
                    branches,
                    branchId,
                  )}
                </strong>
              </span>

              <span>
                Till:{" "}
                <strong className="font-medium text-foreground">
                  {activeTill
                    ? `${activeTill.code} - ${activeTill.name}`
                    : "Not selected"}
                </strong>
              </span>

              <span>
                Warehouse:{" "}
                <strong className="font-medium text-foreground">
                  {activeTill?.warehouse_id
                    ? "Assigned"
                    : "Not configured"}
                </strong>
              </span>

              <span>
                Opened:{" "}
                <strong className="font-medium text-foreground">
                  {currentShift?.opened_at
                    ? new Date(
                        currentShift.opened_at,
                      ).toLocaleString()
                    : "—"}
                </strong>
              </span>
            </div>
          </div>

            {!currentShift ? (
              <div
                className="
                  grid
                  w-full
                  gap-2
                  sm:grid-cols-[minmax(180px,1fr)_120px_auto]
                  lg:w-auto
                "
              >
                <NativeSelect
                  value={selectedTillId}
                  onChange={setSelectedTillId}
                  disabled={
                    tillsQuery.isLoading ||
                    !isBranchScopeReady
                  }
                  placeholder={
                    tillsQuery.isLoading
                      ? "Loading tills"
                      : "Select till"
                  }
                  options={tills.map((till) => ({
                    value: till.id,
                    label: `${till.code} - ${till.name}`,
                  }))}
                />

                <Input
                  value={openingFloat}
                  onChange={(event) =>
                    setOpeningFloat(
                      event.target.value,
                    )
                  }
                  inputMode="decimal"
                  placeholder="Opening float"
                />

                <Button
                  type="button"
                  onClick={openShift}
                  disabled={
                    openTillShift.isPending ||
                    !selectedTillId ||
                    !activeTill?.warehouse_id
                  }
                  className="
                    bg-[var(--hela-navy)]
                    text-white
                    hover:bg-[var(--hela-navy-strong)]
                  "
                >
                  {openTillShift.isPending
                    ? "Opening..."
                    : "Open Shift"}
                </Button>
              </div>
            ) : shiftRequiresTakeover ? (
              <Button
                type="button"
                onClick={() => setTakeoverShiftOpen(true)}
                disabled={takeoverTillShift.isPending}
                className="
                  shrink-0
                  bg-[var(--hela-navy)]
                  text-white
                  hover:bg-[var(--hela-navy-strong)]
                "
              >
                {takeoverTillShift.isPending
                  ? "Transferring..."
                  : "Continue on this device"}
              </Button>
            ) : (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setClosingCash("");
                  setClosingNotes("");
                  setCloseShiftOpen(true);
                }}
                disabled={closeTillShift.isPending}
                className="shrink-0"
              >
                {closeTillShift.isPending
                  ? "Closing..."
                  : "Close Shift"}
              </Button>
            )}
          </section>

        {/* ================================================================
         * Status / Errors
         * ================================================================ */}
        {!isBranchScopeReady ? (
          <Alert>
            <AlertTitle>
              Branch required
            </AlertTitle>

            <AlertDescription>
              Select an active branch from the application header before
              using POS.
            </AlertDescription>
          </Alert>
        ) : null}

        {lastSaleNumber ? (
          <Alert>
            <AlertTitle>
              Checkout complete
            </AlertTitle>

            <AlertDescription>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span>
                  Sale {lastSaleNumber} was accepted. The POS is ready for
                  the next customer.
                </span>

                {lastSaleId ? (
                  <Link
                    to={PATHS.SALES.receipt(
                      lastSaleId,
                    )}
                    className={buttonVariants({
                      size: "sm",
                    })}
                  >
                    View Receipt
                  </Link>
                ) : null}
              </div>
            </AlertDescription>
          </Alert>
        ) : null}

        {checkoutError ? (
          <Alert variant="destructive">
            <AlertTitle>
              Checkout blocked
            </AlertTitle>

            <AlertDescription>
              {checkoutError}
            </AlertDescription>
          </Alert>
        ) : null}

        {/* ================================================================
         * POS Workspace
         * ================================================================ */}
        <div className="relative min-w-0">
          <div
            className={
              isPosOperational
                ? "min-w-0"
                : "pointer-events-none min-w-0 select-none opacity-40"
            }
          >
            <div
              className="
                grid
                min-w-0
                gap-4
                2xl:grid-cols-[minmax(0,1fr)_460px]
              "
            >
          {/* ==============================================================
           * Product Catalogue
           * ============================================================== */}
          <section
            className="
              min-w-0
              rounded-xl
              border
              bg-background
              shadow-sm
            "
          >
            <div className="border-b p-4">
              <div
                className="
                  grid
                  gap-3
                  xl:grid-cols-[minmax(0,1fr)_minmax(280px,0.55fr)]
                "
              >
                <form
                  className="flex min-w-0 gap-2"
                  onSubmit={(event) => {
                    event.preventDefault();

                    setSubmittedProductSearch(
                      productSearchInput,
                    );
                  }}
                >
                  <div className="relative min-w-0 flex-1">
                    <Search
                      className="
                        pointer-events-none
                        absolute
                        left-3
                        top-1/2
                        size-4
                        -translate-y-1/2
                        text-muted-foreground
                      "
                    />

                    <Input
                      value={productSearchInput}
                      onChange={(event) =>
                        setProductSearchInput(
                          event.target.value,
                        )
                      }
                      placeholder="Search medicines and products..."
                      className="pl-9"
                    />
                  </div>

                  <Button
                    type="submit"
                    variant="outline"
                  >
                    Search
                  </Button>
                </form>

                <form
                  className="flex min-w-0 gap-2"
                  onSubmit={(event) => {
                    event.preventDefault();

                    setSubmittedCode(
                      codeInput.trim(),
                    );
                  }}
                >
                  <div className="relative min-w-0 flex-1">
                    <Barcode
                      className="
                        pointer-events-none
                        absolute
                        left-3
                        top-1/2
                        size-4
                        -translate-y-1/2
                        text-muted-foreground
                      "
                    />

                    <Input
                      value={codeInput}
                      onChange={(event) =>
                        setCodeInput(
                          event.target.value,
                        )
                      }
                      placeholder="Scan barcode / enter code"
                      className="pl-9"
                    />
                  </div>

                  <Button
                    type="submit"
                    variant="outline"
                  >
                    Lookup
                  </Button>
                </form>
              </div>

              {productByCodeQuery.isError ? (
                <p className="mt-2 text-sm text-muted-foreground">
                  Product code was not found.
                </p>
              ) : null}
            </div>

            <div className="p-4">
              {productByCodeQuery.data ? (
                <div className="mb-4">
                  <p
                    className="
                      mb-2
                      text-xs
                      font-semibold
                      uppercase
                      tracking-[0.12em]
                      text-muted-foreground
                    "
                  >
                    Code result
                  </p>

                  <ProductRow
                    product={
                      productByCodeQuery.data
                    }
                    availability={
                      productAvailability.get(
                        productByCodeQuery.data.id,
                      )
                    }
                    availabilityLoading={
                      availabilityQuery.isFetching
                    }
                    tillReady={Boolean(
                      activeTill?.warehouse_id,
                    )}
                    onAdd={addProduct}
                  />


                </div>
              ) : null}

              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold">
                    Products
                  </h2>

                  <p className="text-xs text-muted-foreground">
                    Select a product to add it to the current sale.
                  </p>
                </div>

                <Badge variant="secondary">
                  {products.length} shown
                </Badge>
              </div>

              {productsQuery.isLoading ? (
                <div
                  className="
                    flex
                    min-h-40
                    items-center
                    justify-center
                    text-sm
                    text-muted-foreground
                  "
                >
                  Loading products...
                </div>
              ) : products.length === 0 ? (
                <div
                  className="
                    flex
                    min-h-40
                    items-center
                    justify-center
                    rounded-lg
                    border
                    border-dashed
                    text-sm
                    text-muted-foreground
                  "
                >
                  No products matched the current search.
                </div>
              ) : (
                <div
                  className="
                    grid
                    gap-3
                    md:grid-cols-2
                    2xl:grid-cols-3
                  "
                >
                  {products.map((product) => (
                    <ProductRow
                      key={product.id}
                      product={product}
                      availability={
                        productAvailability.get(
                          product.id,
                        )
                      }
                      availabilityLoading={
                        availabilityQuery.isFetching
                      }
                      tillReady={Boolean(
                        activeTill?.warehouse_id,
                      )}
                      onAdd={addProduct}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* ==============================================================
           * Current Sale
           * ============================================================== */}
          <aside
            className="
              min-w-0
              self-start
              rounded-xl
              border
              bg-background
              shadow-sm
              2xl:sticky
              2xl:top-4
            "
          >
            {/* ------------------------------------------------------------
             * Cart Header
             * ------------------------------------------------------------ */}
            <div
              className="
                flex
                items-center
                justify-between
                gap-3
                border-b
                px-4
                py-3
              "
            >
              <div>
                <div className="flex items-center gap-2">
                  <ShoppingCart className="size-4 text-[var(--hela-navy)]" />

                  <h2 className="font-semibold">
                    Current Sale
                  </h2>

                  <Badge variant="secondary">
                    {cartItems.length}
                  </Badge>
                </div>

                <p className="mt-0.5 text-xs text-muted-foreground">
                  {selectedCustomer
                    ? selectedCustomer.full_name
                    : "Walk-in customer"}
                </p>
              </div>

              {cartItems.length > 0 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setCartItems([]);
                    setPrescriptionDrafts({});
                    setCheckoutError(null);
                  }}
                >
                  Clear
                </Button>
              ) : null}
            </div>

            {/* ------------------------------------------------------------
             * Cart Items
             * ------------------------------------------------------------ */}
            <div
              className="
                max-h-[42vh]
                overflow-y-auto
                px-4
                py-2
              "
            >
              {cartItems.length === 0 ? (
                <div
                  className="
                    flex
                    min-h-44
                    flex-col
                    items-center
                    justify-center
                    gap-2
                    text-center
                    text-muted-foreground
                  "
                >
                  <ShoppingCart className="size-8 opacity-40" />

                  <p className="text-sm">
                    No products in the current sale.
                  </p>

                  <p className="text-xs">
                    Search or scan a product to begin.
                  </p>
                </div>
              ) : (
                cartItems.map((item) => (
                  <div
                    key={item.product.id}
                    className="
                      border-b
                      py-3
                      last:border-b-0
                    "
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">
                          {item.product.name}
                        </p>

                        <div
                          className="
                            mt-1
                            flex
                            flex-wrap
                            items-center
                            gap-1.5
                            text-[11px]
                            text-muted-foreground
                          "
                        >
                          <span>
                            {displayProductCode(
                              item.product,
                            )}
                          </span>

                          {item.product.requires_prescription ? (
                            <Badge
                              variant="outline"
                              className="h-5 px-1.5 text-[10px]"
                            >
                              Rx
                            </Badge>
                          ) : null}

                          <AvailabilityBadges
                            product={item.product}
                            availability={
                              productAvailability.get(
                                item.product.id,
                              )
                            }
                            compact
                          />
                        </div>
                      </div>

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="size-8 shrink-0"
                        onClick={() =>
                          removeCartItem(
                            item.product.id,
                          )
                        }
                        aria-label="Remove item"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>

                    <div className="mt-3">
                      <PosProductUnitSelector
                        product={item.product}
                        selectedUnit={item.unit}
                        onChange={(unit) =>
                          updateCartUnit(
                            item.product.id,
                            unit,
                          )
                        }
                      />
                    </div>

                    <div
                      className="
                        mt-3
                        rounded-lg
                        border
                        bg-muted/20
                        p-3
                      "
                    >
                      <div className="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-end">
                        <div className="space-y-1">
                          <p className="text-xs font-medium">
                            Selling Price
                          </p>

                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            inputMode="decimal"
                            value={
                              item.sellingPrice
                            }
                            onChange={(event) =>
                              updateCartSellingPrice(
                                item.product.id,
                                event.target.value,
                              )
                            }
                            className="h-9"
                          />
                        </div>

                        <div className="text-xs text-muted-foreground sm:text-right">
                          <p>
                            Marked:{" "}
                            {money(
                              cartMarkedUnitPrice(
                                item,
                              ),
                            )}
                          </p>

                          {cartMinimumUnitPrice(
                            item,
                          ) !== null ? (
                            <p>
                              Minimum:{" "}
                              {money(
                                cartMinimumUnitPrice(
                                  item,
                                ) ?? 0,
                              )}
                            </p>
                          ) : null}
                        </div>
                      </div>

                      {cartUnitPrice(item) !==
                      cartMarkedUnitPrice(
                        item,
                      ) ? (
                        <p className="mt-2 text-[11px] text-muted-foreground">
                          Price override:{" "}
                          {money(
                            cartUnitPrice(
                              item,
                            ) -
                              cartMarkedUnitPrice(
                                item,
                              ),
                          )}{" "}
                          from marked price
                        </p>
                      ) : null}
                    </div>

                    <div className="mt-3 flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        className="size-8"
                        onClick={() =>
                          updateCartQuantity(
                            item.product.id,
                            String(
                              Math.max(
                                1,
                                quantityValue(
                                  item.quantity,
                                ) - 1,
                              ),
                            ),
                          )
                        }
                        aria-label="Decrease quantity"
                      >
                        <Minus className="size-3.5" />
                      </Button>

                      <Input
                        value={item.quantity}
                        onChange={(event) =>
                          updateCartQuantity(
                            item.product.id,
                            event.target.value,
                          )
                        }
                        inputMode="decimal"
                        className="h-8 w-20 text-center"
                      />

                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        className="size-8"
                        onClick={() =>
                          updateCartQuantity(
                            item.product.id,
                            String(
                              quantityValue(
                                item.quantity,
                              ) + 1,
                            ),
                          )
                        }
                        aria-label="Increase quantity"
                      >
                        <Plus className="size-3.5" />
                      </Button>

                      <div className="ml-auto text-right">
                        <p className="text-xs text-muted-foreground">
                          {money(
                            cartUnitPrice(item),
                          )}{" "}
                          × {item.quantity}
                        </p>

                        <p className="text-sm font-semibold">
                          {money(
                            cartLineTotal(item),
                          )}
                        </p>
                      </div>
                    </div>

                    {item.product.track_inventory ? (
                      <div
                        className="
                          mt-2
                          text-[11px]
                          text-muted-foreground
                        "
                      >
                        Sellable:{" "}
                        {quantity(
                          productAvailability.get(
                            item.product.id,
                          )?.sellable_quantity ??
                            null,
                        )}{" "}
                        base units
                      </div>
                    ) : null}

                    {item.product.requires_prescription ? (
                      <div
                        className="
                          mt-3
                          grid
                          gap-2
                          rounded-lg
                          border
                          bg-muted/20
                          p-3
                        "
                      >
                        <div className="flex items-center gap-2 text-xs font-semibold">
                          <FileText className="size-4" />
                          Prescription details
                        </div>

                        <Input
                          value={
                            prescriptionDrafts[
                              item.product.id
                            ]?.prescriber_name ??
                            ""
                          }
                          onChange={(event) =>
                            updatePrescriptionDraft(
                              item.product.id,
                              {
                                prescriber_name:
                                  event.target.value,
                              },
                            )
                          }
                          placeholder="Prescriber name"
                        />

                        <div className="grid gap-2 sm:grid-cols-2">
                          <Input
                            value={
                              prescriptionDrafts[
                                item.product.id
                              ]
                                ?.prescriber_registration_number ??
                              ""
                            }
                            onChange={(event) =>
                              updatePrescriptionDraft(
                                item.product.id,
                                {
                                  prescriber_registration_number:
                                    event.target
                                      .value,
                                },
                              )
                            }
                            placeholder="Registration no."
                          />

                          <Input
                            type="date"
                            value={
                              prescriptionDrafts[
                                item.product.id
                              ]?.prescription_date ??
                              ""
                            }
                            onChange={(event) =>
                              updatePrescriptionDraft(
                                item.product.id,
                                {
                                  prescription_date:
                                    event.target
                                      .value,
                                },
                              )
                            }
                          />
                        </div>

                        <Input
                          value={
                            prescriptionDrafts[
                              item.product.id
                            ]
                              ?.prescription_reference ??
                            ""
                          }
                          onChange={(event) =>
                            updatePrescriptionDraft(
                              item.product.id,
                              {
                                prescription_reference:
                                  event.target.value,
                              },
                            )
                          }
                          placeholder="Prescription reference"
                        />

                        <Textarea
                          value={
                            prescriptionDrafts[
                              item.product.id
                            ]?.notes ?? ""
                          }
                          onChange={(event) =>
                            updatePrescriptionDraft(
                              item.product.id,
                              {
                                notes:
                                  event.target.value,
                              },
                            )
                          }
                          placeholder="Prescription notes"
                          className="min-h-16"
                        />
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>

            {/* ------------------------------------------------------------
             * Customer
             * ------------------------------------------------------------ */}
            <div className="border-t px-4 py-3">
              <FieldBlock
                label="Customer"
                description={
                  selectedCustomer
                    ? "Customer attached to this sale."
                    : "Walk-in sale unless a customer is selected."
                }
              >
                {selectedCustomer ? (
                  <div
                    className="
                      flex
                      items-center
                      justify-between
                      gap-2
                      rounded-lg
                      border
                      bg-muted/30
                      px-3
                      py-2
                    "
                  >
                    <span className="truncate text-sm font-medium">
                      {selectedCustomer.full_name}
                    </span>

                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setSelectedCustomer(null)
                      }
                    >
                      Clear
                    </Button>
                  </div>
                ) : (
                  <>
                    <form
                      className="flex gap-2"
                      onSubmit={(event) => {
                        event.preventDefault();

                        setSubmittedCustomerSearch(
                          customerSearchInput,
                        );
                      }}
                    >
                      <Input
                        value={customerSearchInput}
                        onChange={(event) =>
                          setCustomerSearchInput(
                            event.target.value,
                          )
                        }
                        placeholder="Search customer"
                      />

                      <Button
                        type="submit"
                        variant="outline"
                      >
                        Search
                      </Button>
                    </form>

                    {customers.length > 0 ? (
                      <div className="mt-2 grid gap-1">
                        {customers.map(
                          (customer) => (
                            <Button
                              key={customer.id}
                              type="button"
                              variant="ghost"
                              className="h-8 justify-start"
                              onClick={() =>
                                setSelectedCustomer(
                                  customer,
                                )
                              }
                            >
                              {customer.full_name}
                            </Button>
                          ),
                        )}
                      </div>
                    ) : null}
                  </>
                )}
              </FieldBlock>
            </div>

            {/* ------------------------------------------------------------
             * Payments
             * ------------------------------------------------------------ */}
            <div className="border-t px-4 py-3">
              <FieldBlock
                label="Payment"
                description={`Entered: ${money(
                  tenderedTotal,
                )}`}
              >
                <div className="grid gap-2">
                  {payments.map((payment) => (
                    <div
                      key={payment.id}
                      className="
                        grid
                        gap-2
                        sm:grid-cols-[1fr_110px]
                      "
                    >
                      <NativeSelect
                        value={
                          payment.payment_method_id
                        }
                        onChange={(value) =>
                          updatePayment(
                            payment.id,
                            {
                              payment_method_id:
                                value,
                            },
                          )
                        }
                        placeholder="Payment method"
                        options={paymentMethods.map(
                          (method) => ({
                            value: method.id,
                            label: method.name,
                          }),
                        )}
                      />

                      <Input
                        value={payment.amount}
                        onChange={(event) =>
                          updatePayment(
                            payment.id,
                            {
                              amount:
                                event.target.value,
                            },
                          )
                        }
                        inputMode="decimal"
                        placeholder="Amount"
                      />

                      <Input
                        value={payment.reference}
                        onChange={(event) =>
                          updatePayment(
                            payment.id,
                            {
                              reference:
                                event.target.value,
                            },
                          )
                        }
                        placeholder="Reference (optional)"
                        className="sm:col-span-2"
                      />

                      {payments.length > 1 ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="justify-self-start sm:col-span-2"
                          onClick={() =>
                            removePayment(
                              payment.id,
                            )
                          }
                        >
                          Remove payment
                        </Button>
                      ) : null}
                    </div>
                  ))}

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="justify-self-start"
                    onClick={() =>
                      setPayments((entries) => [
                        ...entries,
                        makePaymentEntry(),
                      ])
                    }
                  >
                    <Plus className="size-4" />
                    Add split payment
                  </Button>
                </div>
              </FieldBlock>
            </div>

            {/* ------------------------------------------------------------
             * Totals + Checkout
             * ------------------------------------------------------------ */}
            <div
              className="
                border-t
                bg-muted/20
                px-4
                py-4
              "
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Items</span>
                  <span>
                    {cartItems.reduce(
                      (total, item) =>
                        total +
                        quantityValue(
                          item.quantity,
                        ),
                      0,
                    )}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span>Subtotal</span>

                  <span>
                    {money(estimatedTotal)}
                  </span>
                </div>

                <div
                  className="
                    flex
                    items-end
                    justify-between
                    border-t
                    pt-3
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs
                        font-semibold
                        uppercase
                        tracking-[0.12em]
                        text-muted-foreground
                      "
                    >
                      Total
                    </p>

                    <p className="text-2xl font-bold tracking-tight">
                      {money(estimatedTotal)}
                    </p>
                  </div>

                  {tenderedTotal > 0 ? (
                    <div className="text-right text-xs text-muted-foreground">
                      <p>
                        Tendered{" "}
                        <span className="font-medium text-foreground">
                          {money(tenderedTotal)}
                        </span>
                      </p>

                      {amountDue > 0 ? (
                        <p>
                          Balance{" "}
                          <span className="font-medium text-foreground">
                            {money(amountDue)}
                          </span>
                        </p>
                      ) : null}

                      {changeDue > 0 ? (
                        <p className="mt-1 text-sm font-semibold text-foreground">
                          Change{" "}
                          {money(changeDue)}
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                  </div>
                </div>

                {checkoutDisabledReason &&
                !createSale.isPending ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    {checkoutDisabledReason}
                  </p>
                ) : null}

                <Button
                  type="button"
                  onClick={submitCheckout}
                  disabled={isCheckoutDisabled}
                  className="
                    mt-4
                    h-12
                    w-full
                    bg-[var(--hela-navy)]
                    text-base
                    font-semibold
                    text-white
                    hover:bg-[var(--hela-navy-strong)]
                  "
                >
                  {createSale.isPending
                    ? "Completing Sale..."
                    : `Complete Sale · ${money(
                        estimatedTotal,
                      )}`}
                </Button>
              </div>
            </aside>

            {/* Closes Main POS Workspace grid */}
          </div>

          {/* Closes operational enable/disable wrapper */}
        </div>

        {!isPosOperational ? (
          <div
            className="
              pointer-events-none
              absolute
              inset-0
              z-10
              rounded-xl
              bg-background/20
              backdrop-blur-[1px]
            "
          />
        ) : null}

        {/* Closes relative POS Workspace wrapper */}
      </div>
    </PageContent>
            <Dialog
          open={takeoverShiftOpen}
          onOpenChange={(open) => {
            if (!takeoverTillShift.isPending) {
              setTakeoverShiftOpen(open);
            }
          }}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>
                Continue Till Shift on This Device
              </DialogTitle>

              <DialogDescription>
                This till shift is already active on another device.
                Continuing here will transfer the existing shift to
                this session and end POS access for the previous session.
              </DialogDescription>
            </DialogHeader>

            <div
              className="
                grid
                gap-2
                rounded-lg
                border
                bg-muted/20
                p-3
                text-sm
              "
            >
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">
                  Till
                </span>

                <span className="text-right font-medium">
                  {activeTill
                    ? `${activeTill.code} - ${activeTill.name}`
                    : "—"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">
                  Shift opened
                </span>

                <span className="text-right font-medium">
                  {currentShift?.opened_at
                    ? new Date(
                        currentShift.opened_at,
                      ).toLocaleString()
                    : "—"}
                </span>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setTakeoverShiftOpen(false);
                }}
                disabled={takeoverTillShift.isPending}
              >
                Cancel
              </Button>

              <Button
                type="button"
                onClick={takeoverShift}
                disabled={
                  takeoverTillShift.isPending ||
                  !currentShift
                }
                className="
                  bg-[var(--hela-navy)]
                  text-white
                  hover:bg-[var(--hela-navy-strong)]
                "
              >
                {takeoverTillShift.isPending
                  ? "Transferring..."
                  : "Continue on this device"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog
          open={closeShiftOpen}
          onOpenChange={(open) => {
            if (!closeTillShift.isPending) {
              setCloseShiftOpen(open);
            }
          }}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>
                Close Till Shift
              </DialogTitle>

              <DialogDescription>
                Count the physical cash in the
                drawer and enter the actual amount
                below. Hela360 will reconcile the
                shift after closing.
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-5 py-2">
              <div
                className="
                  grid
                  gap-2
                  rounded-lg
                  border
                  bg-muted/20
                  p-3
                  text-sm
                "
              >
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    Till
                  </span>

                  <span className="text-right font-medium">
                    {activeTill
                      ? `${activeTill.code} - ${activeTill.name}`
                      : "—"}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    Opened
                  </span>

                  <span className="text-right font-medium">
                    {currentShift?.opened_at
                      ? new Date(
                          currentShift.opened_at,
                        ).toLocaleString()
                      : "—"}
                  </span>
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="closing-cash">
                  Closing cash
                </Label>

                <Input
                  id="closing-cash"
                  value={closingCash}
                  onChange={(event) =>
                    setClosingCash(
                      event.target.value,
                    )
                  }
                  inputMode="decimal"
                  placeholder="0.00"
                  autoFocus
                />

                <p className="text-xs text-muted-foreground">
                  Enter the physical cash counted
                  in the drawer.
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="closing-notes">
                  Notes
                </Label>

                <Textarea
                  id="closing-notes"
                  value={closingNotes}
                  onChange={(event) =>
                    setClosingNotes(
                      event.target.value,
                    )
                  }
                  placeholder="Optional closing notes"
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  setCloseShiftOpen(false)
                }
                disabled={
                  closeTillShift.isPending
                }
              >
                Cancel
              </Button>

              <Button
                type="button"
                onClick={closeShift}
                disabled={
                  closeTillShift.isPending ||
                  closingCash.trim().length === 0
                }
                className="
                  bg-[var(--hela-navy)]
                  text-white
                  hover:bg-[var(--hela-navy-strong)]
                "
              >
                {closeTillShift.isPending
                  ? "Closing Shift..."
                  : "Close Shift"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
                <Dialog
          open={reconciliationOpen}
          onOpenChange={setReconciliationOpen}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>
                Shift Reconciliation
              </DialogTitle>

              <DialogDescription>
                The till shift has been closed.
                Review the final cash
                reconciliation.
              </DialogDescription>
            </DialogHeader>

            {lastReconciliation ? (
              <div className="grid gap-3 py-2">
                <ReconciliationRow
                  label="Opening float"
                  value={money(
                    decimalValue(
                      lastReconciliation.opening_float,
                    ),
                  )}
                />

                <ReconciliationRow
                  label="Cash sales"
                  value={money(
                    decimalValue(
                      lastReconciliation.cash_sales_total,
                    ),
                  )}
                />

                <ReconciliationRow
                  label="Expected cash"
                  value={money(
                    decimalValue(
                      lastReconciliation.expected_cash,
                    ),
                  )}
                />

                <ReconciliationRow
                  label="Cash counted"
                  value={money(
                    decimalValue(
                      lastReconciliation.closing_cash,
                    ),
                  )}
                />

                <div className="border-t pt-3">
                  <div className="flex items-center justify-between gap-4">
                    <span className="font-semibold">
                      Variance
                    </span>

                    <span
                      className={
                        Math.abs(
                          decimalValue(
                            lastReconciliation.cash_difference,
                          ),
                        ) < 0.005
                          ? "text-lg font-bold"
                          : "text-lg font-bold text-destructive"
                      }
                    >
                      {decimalValue(
                        lastReconciliation.cash_difference,
                      ) > 0
                        ? "+"
                        : ""}
                      {money(
                        decimalValue(
                          lastReconciliation.cash_difference,
                        ),
                      )}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}

            <DialogFooter>
              <Button
                type="button"
                onClick={() =>
                  setReconciliationOpen(false)
                }
                className="
                  bg-[var(--hela-navy)]
                  text-white
                  hover:bg-[var(--hela-navy-strong)]
                "
              >
                Done
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>            
  </Page>
);

function ReconciliationRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-muted-foreground">
        {label}
      </span>

      <span className="font-medium">
        {value}
      </span>
    </div>
  );
}

}
interface FieldBlockProps {
  label: string;
  description?: string;
  children: ReactNode;
}

function FieldBlock({
  label,
  description,
  children,
}: FieldBlockProps) {
  return (
    <div className="grid gap-2">
      <div>
        <Label>{label}</Label>
        {description ? (
          <p className="text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {children}
    </div>
  );
}

function NativeSelect({
  value,
  onChange,
  options,
  placeholder,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{
    value: string;
    label: string;
  }>;
  placeholder: string;
  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      disabled={disabled}
      className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
    >
      <option value="">
        {placeholder}
      </option>
      {options.map((option) => (
        <option
          key={option.value}
          value={option.value}
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}

interface PosProductUnitSelectorProps {
  product: Product;
  selectedUnit: ProductUnit | null;
  onChange: (
    productUnit: ProductUnit | null,
  ) => void;
}


function PosProductUnitSelector({
  product,
  selectedUnit,
  onChange,
}: PosProductUnitSelectorProps) {
  const productUnitsQuery =
    useProductUnits(
      product.id,
    );

  const sellableUnits =
    (
      productUnitsQuery.data ?? []
    ).filter(
      (productUnit) =>
        productUnit.is_active &&
        productUnit.can_sell,
    );

  const handleChange = (
    value: string,
  ) => {
    if (!value) {
      onChange(null);
      return;
    }

    const productUnit =
      sellableUnits.find(
        (unit) =>
          unit.id === value,
      );

    if (!productUnit) {
      return;
    }

    onChange(productUnit);
  };

  return (
    <div className="grid gap-1">
      <Label className="text-xs">
        Selling unit
      </Label>

      <NativeSelect
        value={
          selectedUnit?.id ?? ""
        }
        onChange={handleChange}
        disabled={
          productUnitsQuery.isLoading
        }
        placeholder={
          productUnitsQuery.isLoading
            ? "Loading units"
            : (
                product.unit
                  ? `${product.unit.name} · default`
                  : "Default unit"
              )
        }
        options={
          sellableUnits.map(
            (productUnit) => ({
              value:
                productUnit.id,

              label:
                productUnitLabel(
                  productUnit,
                ),
            }),
          )
        }
      />

      {productUnitsQuery.isError ? (
        <p className="text-xs text-destructive">
          Unable to load additional selling units.
          The product default unit remains available.
        </p>
      ) : null}

      {selectedUnit ? (
        <p className="text-xs text-muted-foreground">
          1{" "}
          {selectedUnit.unit?.name ??
            "unit"}{" "}
          ={" "}
          {quantity(
            selectedUnit
              .conversion_factor_to_base,
          )}{" "}
          base units
          {" · "}
          Selling price{" "}
          {selectedUnit.sale_price !== null
            ? money(
                decimalValue(
                  selectedUnit.sale_price,
                ),
              )
            : "not configured"}
        </p>
      ) : product.unit ? (
        <p className="text-xs text-muted-foreground">
          Default:{" "}
          {product.unit.name}
          {" · "}
          Selling price{" "}
          {product.default_sale_price
            ? money(
                decimalValue(
                  product.default_sale_price,
                ),
              )
            : "not configured"}
        </p>
      ) : null}
    </div>
  );
}

function ProductRow({
  product,
  availability,
  availabilityLoading,
  tillReady,
  onAdd,
}: {
  product: Product;
  availability?: PosProductAvailability;
  availabilityLoading: boolean;
  tillReady: boolean;
  onAdd: (product: Product) => void;
}) {
  const awaitingAvailability =
    product.track_inventory &&
    tillReady &&
    availabilityLoading &&
    !availability;
  const isOutOfStock =
    product.track_inventory &&
    availability?.status === "out_of_stock";
  const disabled =
    !product.is_active ||
    awaitingAvailability ||
    isOutOfStock;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onAdd(product)}
      className="
        group
        flex
        min-h-32
        w-full
        flex-col
        justify-between
        rounded-xl
        border
        bg-background
        p-3
        text-left
        transition
        hover:border-[var(--hela-navy)]
        hover:shadow-sm
        disabled:cursor-not-allowed
        disabled:opacity-50
      "
    >
      <div className="min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="line-clamp-2 text-sm font-semibold leading-snug">
            {product.name}
          </p>

          <Plus
            className="
              size-4
              shrink-0
              text-muted-foreground
              transition-colors
              group-hover:text-[var(--hela-navy)]
            "
          />
        </div>

        <p className="mt-1 truncate text-[11px] text-muted-foreground">
          {displayProductCode(product)}
        </p>

        <div className="mt-2 flex flex-wrap gap-1">
          {product.requires_prescription ? (
            <Badge
              variant="outline"
              className="h-5 px-1.5 text-[10px]"
            >
              Rx
            </Badge>
          ) : null}

          {!product.is_active ? (
            <Badge
              variant="secondary"
              className="h-5 px-1.5 text-[10px]"
            >
              Inactive
            </Badge>
          ) : null}

          <AvailabilityBadges
            product={product}
            availability={availability}
            loading={awaitingAvailability}
            compact
          />
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Price
          </p>

          <p className="font-semibold">
            {money(
              decimalValue(
                product.default_sale_price,
              ),
            )}
          </p>
        </div>

        {product.unit ? (
          <span className="text-[10px] text-muted-foreground">
            {product.unit.code}
          </span>
        ) : null}
      </div>
    </button>
  );
}

function AvailabilityBadges({
  product,
  availability,
  loading = false,
  compact = false,
}: {
  product: Product;
  availability?: PosProductAvailability;
  loading?: boolean;
  compact?: boolean;
}) {
  if (!product.track_inventory) {
    return (
      <Badge variant="outline">
        Non-stock
      </Badge>
    );
  }

  if (loading) {
    return (
      <Badge variant="outline">
        Checking stock
      </Badge>
    );
  }

  if (!availability) {
    return (
      <Badge variant="outline">
        Stock unknown
      </Badge>
    );
  }

  if (availability.status === "out_of_stock") {
    return (
      <>
        <Badge variant="destructive">
          Out of stock
        </Badge>
        {availability.expired_only ? (
          <Badge variant="outline">
            Expired only
          </Badge>
        ) : null}
      </>
    );
  }

  return (
    <>
      <Badge variant={availability.is_low_stock ? "secondary" : "outline"}>
        {availability.is_low_stock ? "Low stock" : "In stock"}
      </Badge>
      {!compact ? (
        <span className="text-xs text-muted-foreground">
          Sellable {quantity(availability.sellable_quantity)}
          {availability.earliest_sellable_expiry_date
            ? ` · Earliest expiry ${dateLabel(availability.earliest_sellable_expiry_date)}`
            : ""}
        </span>
      ) : null}
    </>
  );
}

export default PosPage;
