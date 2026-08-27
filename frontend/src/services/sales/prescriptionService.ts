/**
 * ============================================================================
 * Hela360 Enterprise Prescription Service
 * ============================================================================
 *
 * Service responsible for prescription management and dispensing.
 *
 * Responsibilities
 * ----------------
 * • Prescription CRUD
 * • Prescription lookup
 * • Prescription validation
 * • Dispensing workflow
 * • Refill management
 * • Prescription history
 * • Patient prescriptions
 * • Prescriber prescriptions
 * • Dispensing audit
 *
 * Integrates with:
 *
 * • Customers
 * • Sales
 * • Inventory
 * • Pharmacists
 * • Doctors
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

/* ============================================================================
 * Types
 * ============================================================================
 */

export type PrescriptionStatus =
  | "PENDING"
  | "PARTIALLY_DISPENSED"
  | "DISPENSED"
  | "EXPIRED"
  | "CANCELLED";

export interface PrescriptionItem {
  id: string;

  productId: string;

  productName: string;

  prescribedQuantity: number;

  dispensedQuantity: number;

  remainingQuantity: number;

  dosage: string;

  frequency: string;

  duration: string;

  instructions?: string;
}

export interface Prescription {
  id: string;

  prescriptionNumber: string;

  customerId: string;

  prescriberId?: string;

  prescriberName?: string;

  issueDate: string;

  expiryDate?: string;

  status: PrescriptionStatus;

  notes?: string;

  items: PrescriptionItem[];

  createdAt: string;

  updatedAt: string;
}

export interface CreatePrescriptionRequest {
  customerId: string;

  prescriberId?: string;

  issueDate: string;

  expiryDate?: string;

  notes?: string;

  items: {
    productId: string;

    prescribedQuantity: number;

    dosage: string;

    frequency: string;

    duration: string;

    instructions?: string;
  }[];
}

export interface UpdatePrescriptionRequest {
  expiryDate?: string;

  notes?: string;

  status?: PrescriptionStatus;
}

export interface DispenseItemRequest {
  itemId: string;

  quantity: number;
}

export interface DispensePrescriptionRequest {
  pharmacistId?: string;

  items: DispenseItemRequest[];
}

export interface PrescriptionValidation {
  valid: boolean;

  expired: boolean;

  fullyDispensed: boolean;

  message?: string;
}

/* ============================================================================
 * Prescription Service
 * ============================================================================
 */

export class PrescriptionService extends BaseService<
  Prescription,
  CreatePrescriptionRequest,
  UpdatePrescriptionRequest
> {
  constructor() {
    super(API_ENDPOINTS.PRESCRIPTIONS.ROOT);
  }

  /* ==========================================================================
   * Validation
   * ==========================================================================
   */

  async validate(
    prescriptionId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<PrescriptionValidation>> {
    const response =
      await this.getRequest<ApiResponse<PrescriptionValidation>>(
        `${this.resource}/${prescriptionId}/validate`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Dispensing
   * ==========================================================================
   */

  async dispense(
    prescriptionId: string,
    payload: DispensePrescriptionRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Prescription>> {
    const response =
      await this.postRequest<ApiResponse<Prescription>>(
        `${this.resource}/${prescriptionId}/dispense`,
        payload,
        config,
      );

    return response.data;
  }

  async refill(
    prescriptionId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Prescription>> {
    const response =
      await this.postRequest<ApiResponse<Prescription>>(
        `${this.resource}/${prescriptionId}/refill`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Customer
   * ==========================================================================
   */

  async customerPrescriptions(
    customerId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Prescription[]>> {
    const response =
      await this.getRequest<ApiResponse<Prescription[]>>(
        `${API_ENDPOINTS.CUSTOMERS.ROOT}/${customerId}/prescriptions`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Prescriber
   * ==========================================================================
   */

  async prescriberPrescriptions(
    prescriberId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Prescription[]>> {
    const response =
      await this.getRequest<ApiResponse<Prescription[]>>(
        `${this.resource}/prescribers/${prescriberId}`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * History
   * ==========================================================================
   */

  async history(
    prescriptionId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<unknown[]>> {
    const response =
      await this.getRequest<ApiResponse<unknown[]>>(
        `${this.resource}/${prescriptionId}/history`,
        config,
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const prescriptionService =
  new PrescriptionService();

export default prescriptionService;