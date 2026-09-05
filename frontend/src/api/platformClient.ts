/**
 * ============================================================================
 * Hela360 Platform API Client
 * ============================================================================
 *
 * HTTP client exclusively for Hela360 Office.
 * ============================================================================
 */

import axios, {
  type AxiosInstance,
} from "axios";

import { API } from "@/constants";
import {
  registerPlatformInterceptors,
} from "@/api/platformInterceptors";

const platformApiClient: AxiosInstance =
  axios.create({
    baseURL: API.baseUrl,

    timeout: API.timeout,

    headers: {
      Accept: API.contentType,
      "Content-Type": API.contentType,
    },

    withCredentials: false,
    responseType: "json",
  });

registerPlatformInterceptors(
  platformApiClient,
);

export {
  platformApiClient,
};

export default platformApiClient;
