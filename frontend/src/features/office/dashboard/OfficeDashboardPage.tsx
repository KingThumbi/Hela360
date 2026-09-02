export function OfficeDashboardPage() {
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
          Platform
        </div>

        <h1 className="text-3xl font-semibold tracking-tight">
          Hela360 Office
        </h1>

        <p className="max-w-2xl text-sm text-muted-foreground">
          Platform governance and administration for Hela360.
        </p>
      </div>

      <div
        className="
          mt-8
          rounded-xl
          border
          bg-card
          p-6
          shadow-sm
        "
      >
        <h2 className="text-base font-semibold">
          Office application boundary established
        </h2>

        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          Master Catalogue governance, supplier intelligence,
          tenant oversight, and platform administration will be
          introduced here as separate platform capabilities.
        </p>
      </div>
    </div>
  );
}

export default OfficeDashboardPage;
