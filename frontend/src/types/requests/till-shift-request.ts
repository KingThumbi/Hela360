export interface OpenTillShiftRequest {
  readonly till_id: string;

  readonly opening_float?: string;

  readonly notes?: string | null;
}

export interface CloseTillShiftRequest {
  readonly closing_cash: string;

  readonly notes?: string | null;
}
