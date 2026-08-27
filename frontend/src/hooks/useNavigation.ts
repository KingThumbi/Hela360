import { useMemo } from "react";
import { useLocation } from "react-router-dom";

import {
  filterNavigation,
  filterNavigationSection,
  flattenNavigation,
  navigation,
} from "@/navigation";

import { useAuthorization } from "@/authorization";

import type {
  NavigationItem,
  NavigationSection,
} from "@/types/navigation";


export interface UseNavigationResult {
  navigation: NavigationSection[];

  visibleNavigation: NavigationSection[];

  items: NavigationItem[];

  isActive: (
    href: string,
  ) => boolean;

  isSectionActive: (
    section: NavigationSection,
  ) => boolean;

  getVisibleItems: (
    section: NavigationSection,
  ) => NavigationItem[];
}


export function useNavigation(): UseNavigationResult {
  const pathname =
    useLocation().pathname;

  const authorization =
    useAuthorization();

  const visibleNavigation =
    useMemo(
      () =>
        filterNavigation(
          navigation,
          authorization.can,
        ),
      [authorization.can],
    );

  const items =
    useMemo(
      () =>
        flattenNavigation(
          visibleNavigation,
        ),
      [visibleNavigation],
    );

  const isActive = (
    href: string,
  ): boolean => {
    if (href === "/") {
      return pathname === "/";
    }

    return (
      pathname === href ||
      pathname.startsWith(
        `${href}/`,
      )
    );
  };

  const getVisibleItems = (
    section: NavigationSection,
  ): NavigationItem[] =>
    filterNavigationSection(
      section,
      authorization.can,
    ).items;

  const isSectionActive = (
    section: NavigationSection,
  ): boolean =>
    getVisibleItems(section).some(
      (item) =>
        item.href
          ? isActive(item.href)
          : false,
    );

  return {
    navigation,
    visibleNavigation,
    items,
    isActive,
    isSectionActive,
    getVisibleItems,
  };
}


export default useNavigation;
