export interface OfficeCataloguePlaceholderPageProps {
  eyebrow: string;
  title: string;
  description: string;
}

export function OfficeCataloguePlaceholderPage({
  eyebrow,
  title,
  description,
}: OfficeCataloguePlaceholderPageProps) {
  return (
    <div className="mx-auto w-full max-w-7xl p-6 lg:p-8">
      <div className="space-y-2">
        <div
          className="
            text-xs
            font-semibold
            uppercase
            tracking-[0.16em]
            text-muted-foreground
          "
        >
          {eyebrow}
        </div>

        <h1 className="text-3xl font-semibold tracking-tight">
          {title}
        </h1>

        <p className="max-w-3xl text-sm text-muted-foreground">
          {description}
        </p>
      </div>

      <div
        className="
          mt-8
          rounded-xl
          border
          border-dashed
          bg-card
          p-6
        "
      >
        <div className="text-sm font-medium">
          Governance surface reserved
        </div>

        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          This page currently validates the Hela360 Office application and
          navigation architecture. Operational workflows will be introduced
          only after the corresponding platform authorization and backend
          contracts are established.
        </p>
      </div>
    </div>
  );
}

export default OfficeCataloguePlaceholderPage;
