import {
  ArrowLeft,
  Printer,
} from "lucide-react";
import {
  Link,
  useParams,
} from "react-router-dom";

import {
  Page,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
} from "@/components/page";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import { SaleReceipt } from "@/features/sales/components/SaleReceipt";
import {
  useReceipt,
} from "@/hooks/queries/sales";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PATHS } from "@/routes/routes";

export function SaleReceiptPage() {
  const { saleId = "" } = useParams();
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const receiptQuery = useReceipt(saleId, {
    enabled: saleId.trim().length > 0,
  });

  return (
    <Page>
      <style>
        {`
          @media print {
            body * {
              visibility: hidden;
            }

            .sale-receipt,
            .sale-receipt * {
              visibility: visible;
            }

            .sale-receipt {
              position: absolute;
              inset: 0 auto auto 0;
              width: 80mm;
              padding: 0;
              color: #000;
              background: #fff;
            }

            @page {
              size: 80mm auto;
              margin: 4mm;
            }
          }
        `}
      </style>
      <PageHeader>
        <div>
          <PageTitle>Sales Receipt</PageTitle>
          <PageDescription>
            Printable persisted sale receipt.
          </PageDescription>
        </div>
        <div className="flex gap-2 print:hidden">
          <Link
            to={PATHS.SALES.POS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft className="size-4" />
            POS
          </Link>
          <Button
            type="button"
            onClick={() => window.print()}
            disabled={!receiptQuery.data}
          >
            <Printer className="size-4" />
            Print
          </Button>
        </div>
      </PageHeader>

      <PageContent>
        {!isBranchScopeReady ? (
          <Alert>
            <AlertTitle>Branch required</AlertTitle>
            <AlertDescription>
              Select an active branch before viewing receipts.
            </AlertDescription>
          </Alert>
        ) : null}

        {receiptQuery.isLoading ? (
          <PageSection>
            <p className="text-sm text-muted-foreground">
              Loading receipt...
            </p>
          </PageSection>
        ) : null}

        {receiptQuery.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Receipt unavailable</AlertTitle>
            <AlertDescription>
              {receiptQuery.error.message}
            </AlertDescription>
          </Alert>
        ) : null}

        {receiptQuery.data ? (
          <PageSection>
            <SaleReceipt receipt={receiptQuery.data} />
          </PageSection>
        ) : null}
      </PageContent>
    </Page>
  );
}

export default SaleReceiptPage;
