import {
  useMemo,
  useState,
} from "react";

import { storage } from "@/lib/storage";
import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";

/**
 * ============================================================================
 * useCurrentBranch
 * ============================================================================
 *
 * Provides the active branch context for the application shell.
 *
 * This hook intentionally hides where the active branch originates.
 * Components should always consume this hook instead of reading from the
 * shell store or authentication state directly.
 *
 * Current Source
 * --------------
 * The selected branch is maintained by the Shell Store.
 *
 * Future Sources
 * --------------
 * The implementation may later resolve the active branch from:
 *
 * • Backend AuthorizationContext
 * • JWT claims
 * • /auth/me endpoint
 * • Tenant context
 * • Branch switching service
 *
 * None of those changes should require updates to consuming components.
 * ============================================================================
 */

/**
 * Active branch information exposed to the UI.
 */
export interface BranchContext {
  /**
   * Branch identifier.
   */
  id: string;

  /**
   * Human-friendly branch code.
   */
  code: string;

  /**
   * Display name.
   */
  name: string;
}

/**
 * Hook result.
 */
export interface UseCurrentBranchResult {
  /**
   * Active branch.
   */
  branch?: BranchContext;

  /**
   * Available branches for the selector.
   */
  branches: BranchContext[];

  /**
   * Active branch identifier.
   */
  branchId?: string;

  /**
   * Indicates whether a branch is currently active.
   */
  hasBranch: boolean;

  /**
   * Selector open state.
   */
  isOpen: boolean;

  /**
   * Opens the selector.
   */
  open: () => void;

  /**
   * Closes the selector.
   */
  close: () => void;

  /**
   * Updates the selected branch.
   *
   * This currently updates the shell state only. Future implementations
   * may synchronize the selection with the backend or an authorization
   * context without changing the hook's public API.
   */
  setBranch: (branchId?: string) => void;
}

export function useCurrentBranch(): UseCurrentBranchResult {
  const [isOpen, setIsOpen] = useState(false);

  /**
   * Current shell state.
   */
  const branchId = useShellStore(
    (state) => state.selectedBranchId,
  );

  const setSelectedBranch = useShellStore(
    (state) => state.setSelectedBranch,
  );

  const accessibleBranches = useAuthStore(
    (state) => state.accessibleBranches,
  );

  /**
   * Resolve the active branch.
   *
   * This placeholder implementation derives a minimal BranchContext from
   * the selected branch identifier. In future this object will be resolved
   * from the authenticated AuthorizationContext or a branch service.
   */
  const branch = useMemo<BranchContext | undefined>(() => {
    if (!branchId) {
      return undefined;
    }

    const accessibleBranch =
      accessibleBranches.find(
        (candidate) => candidate.id === branchId,
      );

    if (!accessibleBranch) {
      return undefined;
    }

    return {
      id: accessibleBranch.id,
      code: accessibleBranch.code,
      name: accessibleBranch.name,
    };
  }, [accessibleBranches, branchId]);

  const branches = useMemo<BranchContext[]>(
    () =>
      accessibleBranches.map((candidate) => ({
        id: candidate.id,
        code: candidate.code,
        name: candidate.name,
      })),
    [accessibleBranches],
  );

  const setBranch = (nextBranchId?: string) => {
    if (!nextBranchId) {
      storage.removeBranchId();
      setSelectedBranch(undefined);

      return;
    }

    const isAccessible =
      accessibleBranches.some(
        (candidate) =>
          candidate.id === nextBranchId,
      );

    if (!isAccessible) {
      storage.removeBranchId();
      setSelectedBranch(undefined);

      return;
    }

    storage.setBranchId(nextBranchId);
    setSelectedBranch(nextBranchId);
  };

  return {
    branch,
    branches,
    branchId,

    hasBranch: branch !== undefined,

    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),

    setBranch,
  };
}

export default useCurrentBranch;
